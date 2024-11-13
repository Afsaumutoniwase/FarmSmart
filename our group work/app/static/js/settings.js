document.addEventListener("DOMContentLoaded", () => {
    const formElements = document.querySelectorAll('.settings-item input, .settings-item select, .settings-item textarea');
    
    formElements.forEach(element => {
        element.addEventListener('change', handleFormChange);
    });

    function handleFormChange(event) {
        const { id, value, type, checked } = event.target;

        if (type === 'checkbox') {
            console.log(`Setting ${id} updated to: ${checked}`);
        } else {
            console.log(`Setting ${id} updated to: ${value}`);
        }
    }

    const reportProblemButton = document.getElementById('report-problem');
    reportProblemButton.addEventListener('click', () => {
        alert('Problem reported successfully!');
    });

    const submitFeedbackButton = document.getElementById('submit-feedback');
    submitFeedbackButton.addEventListener('click', () => {
        alert('Feedback submitted successfully!');
    });

    const contactSupportButton = document.getElementById('contact-support');
    contactSupportButton.addEventListener('click', () => {
        alert('Contacting support...');
    });
});
