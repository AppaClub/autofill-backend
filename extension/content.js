// content.js

(async function() {
    // Function to extract form fields from the page.
    function getFormFields() {
      const fields = [];
      const inputs = document.querySelectorAll('input, select, textarea');
      inputs.forEach(input => {
        const field = {};
        let labelElement = null;
  
        // Try to find the label using the 'for' attribute.
        if (input.id) {
          labelElement = document.querySelector(`label[for="${input.id}"]`);
        }
  
        // If not found, check parent elements.
        if (!labelElement) {
          let parent = input.parentElement;
          while (parent && parent !== document.body) {
            if (parent.tagName.toLowerCase() === 'label') {
              labelElement = parent;
              break;
            }
            parent = parent.parentElement;
          }
        }
  
        if (labelElement) {
          field.label = labelElement.innerText.trim().replace(':', '');
        } else {
          field.label = input.placeholder || input.name || '';
        }
  
        field.id = input.id || input.name || '';
        field.type = input.type || '';
  
        if (field.label && field.id) {
          fields.push(field);
        }
      });
      return fields;
    }
  
    // Function to fill in the form fields.
    function fillFormFields(autofillData) {
      Object.keys(autofillData).forEach(fieldId => {
        const inputs = document.querySelectorAll(`#${fieldId}, [name="${fieldId}"]`);
        inputs.forEach(input => {
          if (input.type === 'radio' || input.type === 'checkbox') {
            if (input.value === autofillData[fieldId]) {
              input.checked = true;
            }
          } else {
            input.value = autofillData[fieldId];
          }
        });
      });
    }
  
    // Check if the page has any forms.
    if (!document.forms.length) {
      console.log('No forms detected on this page.');
      return;
    }
  
    // Extract form fields.
    const formFields = getFormFields();
  
    if (formFields.length === 0) {
      console.log('No form fields detected.');
      return;
    }
  
    // Send data to the backend.
    try {
      const response = await fetch('http://localhost:5055/api/get_autofill_data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ form_fields: formFields })
      });
  
      if (response.ok) {
        const autofillData = await response.json();
        // Fill in the form fields.
        fillFormFields(autofillData);
        console.log('Form autofill completed.');
      } else {
        console.error('Error fetching autofill data:', response.statusText);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  })();
  