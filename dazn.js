function clickSecondButtonAndTypeInTextarea() {
    // Get all rows in the table
    const rows = document.querySelectorAll('table tr');
    
    // Check if there are at least two rows
    if (rows.length > 1) {
      // Get the second row (index 1 since it's zero-based)
      const secondRow = rows[1];
  
      // Find all images with the specific src inside the second row
      const images = secondRow.querySelectorAll('img[src="/backoffice/static/media/edit.6d846ca1.svg"]');
      
      // Check if there are at least two images
      if (images.length > 1) {
        // Get the second image (index 1)
        const secondImage = images[1];
  
        // Find the closest button related to the second image and click it
        const button = secondImage.closest('button');
        if (button) {
          button.click();
          console.log("Second button clicked!");
          
          // Wait for 1 second before writing in the textarea
          setTimeout(() => {
            // Find the textarea (adjust the selector as per your DOM structure)
            const textarea = document.querySelector('textarea');
            if (textarea) {
              textarea.value = "Test"; // Set the value
              textarea.dispatchEvent(new Event('input')); // Trigger the input event if needed
              console.log("Wrote 'Test' in the textarea!");
            } else {
              console.log("Textarea not found.");
            }
          }, 1000); // Wait for 1 second (1000 milliseconds)
          
        } else {
          console.log("No button found near the second image.");
        }
      } else {
        console.log("There are not enough images with the given source.");
      }
    } else {
      console.log("There are not enough rows in the table.");
    }
  }
  