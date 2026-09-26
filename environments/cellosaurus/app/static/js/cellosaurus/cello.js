document.addEventListener("DOMContentLoaded", () => {

    // Cache collections
    const moreAuthorsSections = document.querySelectorAll(".more-authors");
    const moreButtons = document.querySelectorAll(".button-more-authors");
    const lessButtons = document.querySelectorAll(".button-less-authors");

    // Initial state
    moreAuthorsSections.forEach(section => {
        section.style.display = "none";
    });

    lessButtons.forEach(button => {
        button.style.display = "none";
    });

    // Show more authors
    moreButtons.forEach(button => {
        button.addEventListener("click", function() {

            const moreAuthorsSection = this.nextElementSibling;
            const lessButton = moreAuthorsSection?.nextElementSibling;

            if (!moreAuthorsSection || !lessButton) return;

            moreAuthorsSection.style.display = "";
            lessButton.style.display = "";
            this.style.display = "none";
        });
    });

    // Hide extra authors
    lessButtons.forEach(button => {
        button.addEventListener("click", function() {

            const moreAuthorsSection = this.previousElementSibling;
            const moreButton = moreAuthorsSection?.previousElementSibling;

            if (!moreAuthorsSection || !moreButton) return;

            moreAuthorsSection.style.display = "none";
            moreButton.style.display = "";
            this.style.display = "none";
        });
    });

});



