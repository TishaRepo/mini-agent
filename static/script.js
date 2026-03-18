document.getElementById('submit-btn').addEventListener('click', async () => {
    const promptInput = document.getElementById('prompt-input');
    const promptText = promptInput.value.trim();
    
    if (!promptText) {
        promptInput.style.borderColor = 'var(--error)';
        setTimeout(() => promptInput.style.borderColor = '', 1000);
        return;
    }

    const btn = document.getElementById('submit-btn');
    const resultsSection = document.getElementById('results-section');
    
    // UI Loading State
    btn.disabled = true;
    btn.classList.add('loading');
    const span = btn.querySelector('span');
    span.innerText = 'Processing...';
    resultsSection.classList.add('hidden');

    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: promptText })
        });

        const data = await response.json();
        
        // Restore UI
        btn.disabled = false;
        btn.classList.remove('loading');
        span.innerText = 'Process Request';
        
        renderResults(data, response.ok);
    } catch (error) {
        btn.disabled = false;
        btn.classList.remove('loading');
        btn.querySelector('span').innerText = 'Process Request';
        alert("Failed to connect to the server.");
    }
});

function renderResults(data, ok) {
    const resultsSection = document.getElementById('results-section');
    const statusBanner = document.getElementById('status-banner');
    const statusIcon = document.getElementById('status-icon');
    const statusText = document.getElementById('status-text');
    const messageBox = document.getElementById('message-box');
    const timeline = document.getElementById('timeline');
    
    resultsSection.classList.remove('hidden');
    
    // Clear previous classes
    statusBanner.className = 'status-banner';
    timeline.innerHTML = '';

    if (!ok && !data.status) {
        // Handle HTTP Error gracefully if structure differs
        data = {
            status: 'error',
            message: data.detail || 'An unknown error occurred.',
            steps_executed: []
        };
    }

    // Set Status Branding
    statusBanner.classList.add(data.status);
    
    if (data.status === 'success') {
        statusIcon.innerText = '✨';
        statusText.innerText = 'Success';
        statusText.style.color = 'var(--success)';
    } else if (data.status === 'failed') {
        statusIcon.innerText = '⚠️';
        statusText.innerText = 'Partially Failed';
        statusText.style.color = '#d29922'; // Warning color
    } else {
        statusIcon.innerText = '❌';
        statusText.innerText = 'Error';
        statusText.style.color = 'var(--error)';
    }

    // Set Message
    messageBox.innerText = data.message;

    // Render Execution Steps Pipeline
    if (data.steps_executed && data.steps_executed.length > 0) {
        data.steps_executed.forEach((step, index) => {
            const isSuccess = step.result?.success !== false;
            
            const card = document.createElement('div');
            card.className = `step-card ${isSuccess ? 'success' : 'error'}`;
            // Stagger animations chronologically
            card.style.animation = `slideUp 0.3s ease-out ${index * 0.15}s both`;
            
            const paramsStr = JSON.stringify(step.parameters, null, 2);
            const resultStr = JSON.stringify(step.result, null, 2);

            card.innerHTML = `
                <div class="step-indicator"></div>
                <div class="step-content">
                    <div class="step-title">${step.action}()</div>
                    <div class="step-params">
                        <span class="label">Parameters Analyzed:</span>
                        <div class="pre-block">${paramsStr}</div>
                    </div>
                    <div class="step-result">
                        <span class="label">Execution Result:</span>
                        <div class="pre-block" style="color: ${isSuccess ? '#7ee787' : '#ff7b72'}">${resultStr}</div>
                    </div>
                </div>
            `;
            timeline.appendChild(card);
        });
    }
}
