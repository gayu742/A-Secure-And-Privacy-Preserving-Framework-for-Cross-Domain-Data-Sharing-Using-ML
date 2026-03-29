async function revealSecret(id) {
    // User kitta irunthu Secret Key vanguroom
    let key = prompt("⚠️ Security Check: Enter the 6-digit Secret Key generated for you:");
    
    if (key) {
        let formData = new FormData();
        formData.append('key', key);
        
        try {
            // Backend endpoint-ku request anupurom
            let resp = await fetch('/decrypt_data/' + id, { 
                method: 'POST', 
                body: formData 
            });
            
            let result = await resp.json();
            
            if (result.status === 'success') {
                // Success aana data-va alert-la kaaturoom
                alert("✅ Decrypted Content Unlocked:\n\n" + result.data);
            } else {
                // Key thappu na error message
                alert("❌ Access Denied: " + result.message);
            }
        } catch (error) {
            console.error("Error fetching data:", error);
            alert("Connection error! Please check if the server is running.");
        }
    }
}

// Button click sounds or hover effects trigger (Optional)
document.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('mousedown', () => {
        btn.style.transform = "scale(0.95)";
    });
    btn.addEventListener('mouseup', () => {
        btn.style.transform = "translateY(-3px)";
    });
});