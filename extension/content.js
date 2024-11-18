(function () {
    const fields = [];
    const processedPages = new Set(); // Track pages already processed
    const filledFields = new Set();   // Track fields that have been filled
    let currentBatchIndex = 0;        // Track the current batch of fields being sent

    function detectFormFields(pageContainer) {
        const pageNumber = pageContainer.dataset.pageNumber;
        console.log(`Scanning page ${pageNumber} for form fields...`);

        if (processedPages.has(pageNumber)) {
            console.log(`Page ${pageNumber} has already been processed. Skipping...`);
            return;
        }

        const annotationLayer = pageContainer.querySelector('.annotationLayer');
        if (!annotationLayer) {
            console.warn(`Annotation layer not found for page ${pageNumber}. Waiting for it...`);
            waitForAnnotationLayer(pageContainer);
            return;
        }

        console.log(`Annotation layer found for page ${pageNumber}.`);

        setTimeout(() => {
            const inputs = annotationLayer.querySelectorAll('input, select, textarea');
            console.log(`Found ${inputs.length} input elements on page ${pageNumber}.`);

            inputs.forEach(input => {
                const field = {
                    id: input.id || input.name || '',
                    label: input.name || input.placeholder || '',
                    type: input.type || '',
                    // context: getFieldContext(input)
                };

                if (field.id && field.label && !filledFields.has(field.id)) {
                    fields.push(field);
                }
            });

            console.log(`Detected ${inputs.length} form fields on page ${pageNumber}.`);

            if (inputs.length > 0) {
                processedPages.add(pageNumber); // Mark this page as processed
                console.log(`Preparing to send detected fields from page ${pageNumber} to the backend in batches.`);
                sendFieldsInBatches(); // Start sending fields in batches
            }
        }, 100);  // Small delay to ensure inputs are rendered
    }
    function getFieldContext(input) {
        const label = input.closest('label')?input.closest('label').innerText : '';
        const surroundingText = input.closest('form') ? input.closest('form').innerText : '';
        return { label, surroundingText };
    }
    function waitForAnnotationLayer(pageContainer) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach(node => {
                    if (node.classList && node.classList.contains('annotationLayer')) {
                        console.log(`Annotation layer found for page ${pageContainer.dataset.pageNumber}.`);
                        observer.disconnect(); // Stop observing once found
                        detectFormFields(pageContainer); // Detect fields once annotation is ready
                    }
                });
            });
        });

        observer.observe(pageContainer, { childList: true, subtree: true });
    }

    function sendFieldsInBatches() {
        if (currentBatchIndex >= fields.length) {
            console.log('All fields have been sent and filled.');
            return; // All fields are processed
        }

        const batch = fields.slice(currentBatchIndex, currentBatchIndex + 4); // Get next 4 fields
        console.log(`Sending batch ${currentBatchIndex / 4 + 1}:`, batch);

        fetch('http://localhost:5055/api/get_autofill_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ form_fields: batch })
        })
            .then(response => {
                if (!response.ok) {
                    console.error('Error fetching autofill data:', response.statusText);
                    return;
                }
                return response.json();
            })
            .then(autofillData => {
                if (autofillData) {
                    fillFormFields(autofillData);
                    console.log(`Batch ${currentBatchIndex / 4 + 1} autofill completed.`);
                    currentBatchIndex += 4; // Move to the next batch
                    sendFieldsInBatches(); // Send the next batch after filling this one
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }

    function fillFormFields(autofillData) {
        Object.keys(autofillData).forEach(fieldId => {
            const inputs = document.querySelectorAll(`#${fieldId}, [name="${fieldId}"]`);
            inputs.forEach(input => {
                if (!filledFields.has(fieldId)) { // Fill only if not already filled
                    if (input.type === 'radio' || input.type === 'checkbox') {
                        input.checked = (input.value === autofillData[fieldId]);
                    } else {
                        input.value = autofillData[fieldId];
                    }
                    filledFields.add(fieldId); // Mark the field as filled
                    // Simulate user input to trigger field change
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        });
    }

    function observePdfViewer() {
        const viewer = document.getElementById('viewer');
        if (!viewer) {
            console.error('PDF viewer element not found.');
            return;
        }
        console.log('PDF viewer found. Adding MutationObserver...');

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach(node => {
                    if (node.classList && node.classList.contains('page')) {
                        console.log(`New page detected: ${node.dataset.pageNumber}`);
                        detectFormFields(node); // Start scanning for form fields
                    }
                });
            });
        });

        observer.observe(viewer, { childList: true, subtree: true });
        console.log('MutationObserver attached to PDF viewer.');
    }

    console.log('Observing PDF viewer for page rendering using MutationObserver...');
    observePdfViewer();  // Start monitoring the viewer for page changes
})();
