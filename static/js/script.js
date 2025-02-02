document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("registrationForm");
    if (form) {
      form.addEventListener("submit", function(e) {
        const emailInput = document.getElementById("email");
        if (!validateEmail(emailInput.value)) {
          alert("Please enter a valid email address.");
          e.preventDefault();
        }
      });
    }
  
    function validateEmail(email) {
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return re.test(email);
    }
  });
  