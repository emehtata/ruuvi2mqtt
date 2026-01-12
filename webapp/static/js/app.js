// Notification system
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Add MQTT Broker
document.getElementById('add-broker-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        name: document.getElementById('broker-name').value,
        host: document.getElementById('broker-host').value,
        port: parseInt(document.getElementById('broker-port').value)
    };

    try {
        const response = await fetch('/api/brokers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Broker added successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error adding broker', 'error');
        console.error('Error:', error);
    }
});

// Delete MQTT Broker
async function deleteBroker(name) {
    if (!confirm(`Delete broker "${name}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/brokers/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Broker deleted successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error deleting broker', 'error');
        console.error('Error:', error);
    }
}

// Add RuuviTag
document.getElementById('add-ruuvi-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        mac: document.getElementById('ruuvi-mac').value.toUpperCase(),
        name: document.getElementById('ruuvi-name').value
    };

    try {
        const response = await fetch('/api/ruuvis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('RuuviTag added successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error adding RuuviTag', 'error');
        console.error('Error:', error);
    }
});

// Delete RuuviTag
async function deleteRuuvi(mac) {
    if (!confirm(`Delete RuuviTag "${mac}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/ruuvis/${encodeURIComponent(mac)}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('RuuviTag deleted successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error deleting RuuviTag', 'error');
        console.error('Error:', error);
    }
}

// Auto-format MAC address input
document.getElementById('ruuvi-mac').addEventListener('input', (e) => {
    let value = e.target.value.toUpperCase().replace(/[^A-F0-9]/g, '');
    let formatted = '';

    for (let i = 0; i < value.length && i < 12; i++) {
        if (i > 0 && i % 2 === 0) {
            formatted += ':';
        }
        formatted += value[i];
    }

    e.target.value = formatted;
});
