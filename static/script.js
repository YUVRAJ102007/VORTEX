let scanner;

function startScanner() {
    scanner = new Html5Qrcode("reader");

    scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        (decodedText) => {

            scanner.stop();

            document.getElementById("result").innerHTML = "Verifying...";

            fetch('/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ data: decodedText })
            })
            .then(res => res.json())
            .then(data => {

                let color = "red";
                if (data.status === "GENUINE") color = "#00ff88";
                else if (data.status === "EXPIRED") color = "#ffd700";
                else if (data.status === "DUPLICATE") color = "orange";

                document.getElementById("result").innerHTML = `
                <div class="card" style="border-color:${color}">
                    <h2>${data.status}</h2>
                    <p>${data.name}</p>
                    <p>Expiry: ${data.expiry}</p>
                    <p>${data.salt}</p>
                </div>`;
            });
        }
    ).catch(err => {
        document.getElementById("result").innerHTML =
            "Camera Error: " + err;
    });
}

function restartScan() {
    document.getElementById("result").innerHTML = "";
    startScanner();
}

window.onload = startScanner;
