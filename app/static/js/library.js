document.addEventListener("DOMContentLoaded", function () {
  // Attach event listeners to all delete buttons
  document.querySelectorAll(".delete-book-btn").forEach((btn) => {
    btn.addEventListener("click", async function (e) {
      e.preventDefault();

      const userBookId = this.dataset.id;
      const confirmed = confirm("Are you sure you want to delete this book?");
      if (!confirmed) return;

      try {
        const tokenRes = await fetch('/csrf-token');
        const tokenData = await tokenRes.json();

        const res = await fetch(`/delete_book/${userBookId}`, {
          method: "DELETE",
          headers: {
            "X-CSRFToken": tokenData.csrf_token
          }
        });



        
        if (!res.ok) {
          const data = await res.json();
          alert(data.error || "An error occurred while deleting the book.");
          return;
        }

        // Remove the book card from the DOM
        this.closest(".book-card").remove();
      } catch (err) {
        console.error("Error deleting book:", err);
        alert("Failed to communicate with the server.");
      }
    });
  });
});
