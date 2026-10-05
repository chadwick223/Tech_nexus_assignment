document.addEventListener("DOMContentLoaded", () => {
    fetchCart();
    fetchInventory();

    // Setup Event Listeners
    document.getElementById("btn-clear").addEventListener("click", () => clearCart());
    document.getElementById("btn-checkout").addEventListener("click", () => checkout());
    
    // Command Form Submit
    document.getElementById("command-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = document.getElementById("command-text").value;
        const fileInput = document.getElementById("command-image");
        const file = fileInput.files[0];

        if (!text && !file) return;

        const formData = new FormData();
        if (text) formData.append("text", text);
        if (file) formData.append("image", file);

        await sendCommand(formData);
        
        // Reset form
        document.getElementById("command-text").value = "";
        fileInput.value = "";
        document.getElementById("file-name").innerText = "No file chosen";
    });

    // File Input Name update
    document.getElementById("command-image").addEventListener("change", (e) => {
        const name = e.target.files[0] ? e.target.files[0].name : "No file chosen";
        document.getElementById("file-name").innerText = name;
    });

    // Setup Voice Recording
    setupVoiceRecording();
});

// --- API Functions ---
const API_BASE = "/cart";

async function fetchCart() {
    try {
        const res = await fetch(API_BASE + "/");
        const cart = await res.json();
        renderCart(cart);
    } catch (e) {
        console.error("Failed to fetch cart", e);
    }
}

async function fetchInventory() {
    try {
        const res = await fetch("/inventory/");
        const inventory = await res.json();
        const select = document.getElementById("manual-item-select");
        select.innerHTML = '<option value="" disabled selected>Select an item...</option>';
        
        for (const [id, data] of Object.entries(inventory)) {
            const name = id.replace("_", " ");
            const option = document.createElement("option");
            option.value = id;
            option.textContent = `${name} (₹${data.price})`;
            select.appendChild(option);
        }
    } catch (e) {
        console.error("Failed to fetch inventory", e);
    }
}

async function manualAdd() {
    const select = document.getElementById("manual-item-select");
    const qtyInput = document.getElementById("manual-qty");
    
    const item_id = select.value;
    const quantity = parseInt(qtyInput.value);
    
    if (!item_id || quantity <= 0) return;
    
    await fetch(`${API_BASE}/items/${item_id}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quantity })
    });
    
    fetchCart();
    qtyInput.value = 1; // Reset qty
    select.selectedIndex = 0; // Reset select
}

async function updateItem(item_id, quantity) {
    if (quantity <= 0) {
        await deleteItem(item_id);
        return;
    }
    await fetch(`${API_BASE}/items/${item_id}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quantity })
    });
    fetchCart();
}

async function deleteItem(item_id) {
    await fetch(`${API_BASE}/items/${item_id}/`, { method: "DELETE" });
    fetchCart();
}

async function clearCart() {
    await fetch(API_BASE + "/", { method: "DELETE" });
    fetchCart();
}

function checkout() {
    // In a real app, you'd save the order to a DB. Here we just clear the cart.
    alert("Order finalized successfully!");
    clearCart();
}

async function sendCommand(formData) {
    const btn = document.getElementById("btn-submit");
    if(btn) btn.innerText = "Processing...";
    
    try {
        const res = await fetch(`${API_BASE}/process/command/`, {
            method: "POST",
            body: formData
        });
        
        if (res.ok) {
            const data = await res.json();
            showFeedback(`AI extracted: ${data.interpreted_action} ${data.interpreted_items.length} item(s)`);
            renderCart(data.cart);
        } else {
            const err = await res.json();
            showFeedback(`Error: ${err.error || err.message || "Failed to process command"}`, true);
        }
    } catch (e) {
        showFeedback("Network error occurred.", true);
    } finally {
        if(btn) btn.innerText = "Send Command";
    }
}

// --- UI Rendering ---

function renderCart(cart) {
    const tbody = document.getElementById("cart-body");
    tbody.innerHTML = "";

    const items = cart.items || {};
    let hasItems = false;
    let computedGrandTotal = 0;

    for (const [id, data] of Object.entries(items)) {
        hasItems = true;
        const tr = document.createElement("tr");
        
        const price = data.price || 0;
        const total = data.total_price || (data.quantity * price);
        computedGrandTotal += total;

        tr.innerHTML = `
            <td class="item-name">${id.replace("_", " ")}</td>
            <td>
                <div class="qty-controls">
                    <button onclick="updateItem('${id}', ${data.quantity - 1})">-</button>
                    <span>${data.quantity}</span>
                    <button onclick="updateItem('${id}', ${data.quantity + 1})">+</button>
                </div>
            </td>
            <td>₹${price.toFixed(2)}</td>
            <td>₹${total.toFixed(2)}</td>
            <td>
                <button class="btn-icon btn-delete" onclick="deleteItem('${id}')">✕</button>
            </td>
        `;
        tbody.appendChild(tr);
    }

    if (!hasItems) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #777;">Cart is empty</td></tr>`;
    }

    const grandTotal = cart.grand_total !== undefined ? cart.grand_total : computedGrandTotal;
    document.getElementById("grand-total-amount").innerText = `₹${grandTotal.toFixed(2)}`;
}

function showFeedback(msg, isError=false) {
    const box = document.getElementById("ai-feedback");
    box.innerText = msg;
    box.classList.remove("hidden");
    box.style.borderColor = isError ? "var(--danger)" : "var(--success)";
    box.style.background = isError ? "rgba(255, 61, 0, 0.1)" : "rgba(0, 200, 83, 0.1)";
    
    setTimeout(() => {
        box.classList.add("hidden");
    }, 5000);
}

// --- Voice Recording Logic (Ported from voice_ui.html) ---
let audioContext, analyser, microphone, scriptProcessor;
let isRecording = false;
let mediaRecorder;
let audioChunks = [];
let silenceStart = Date.now();
const SILENCE_THRESHOLD = 2000; // 2 seconds of silence
const VOLUME_THRESHOLD = 5;

async function setupVoiceRecording() {
    const btn = document.getElementById("btn-record");
    
    btn.addEventListener("click", async () => {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);
        scriptProcessor = audioContext.createScriptProcessor(2048, 1, 1);

        analyser.smoothingTimeConstant = 0.8;
        analyser.fftSize = 1024;

        microphone.connect(analyser);
        analyser.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);

        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            if (audioChunks.length > 0) {
                const blob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append("audio", blob, "voice_command.webm");
                
                document.getElementById("voice-status").innerText = "Processing audio with AI...";
                await sendCommand(formData);
                document.getElementById("voice-status").innerText = "Ready to record...";
            }
        };

        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        const btn = document.getElementById("btn-record");
        btn.classList.add("recording");
        document.getElementById("record-text").innerText = "Stop Listening";
        document.getElementById("voice-status").innerText = "Listening... speak now.";

        // Monitor Audio Volume
        scriptProcessor.onaudioprocess = function() {
            const array = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(array);
            
            let values = 0;
            const length = array.length;
            for (let i = 0; i < length; i++) {
                values += (array[i]);
            }
            const average = values / length;

            if (average > VOLUME_THRESHOLD) {
                silenceStart = Date.now(); // Reset silence timer
            } else {
                if (Date.now() - silenceStart > SILENCE_THRESHOLD && isRecording) {
                    // Auto-stop after silence
                    stopRecording();
                }
            }
        };

    } catch (err) {
        console.error("Error accessing microphone:", err);
        alert("Could not access microphone.");
    }
}

function stopRecording() {
    if (!isRecording) return;
    
    mediaRecorder.stop();
    microphone.disconnect();
    scriptProcessor.disconnect();
    isRecording = false;

    // Update UI
    const btn = document.getElementById("btn-record");
    btn.classList.remove("recording");
    document.getElementById("record-text").innerText = "Start Listening";
}
