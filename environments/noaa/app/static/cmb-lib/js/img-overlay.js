function imgClick(){}

document.addEventListener("DOMContentLoaded", () => {

    // Create modal once
    const modal = document.createElement("div");
    modal.id = "image-modal";
    modal.className = "modal fade text-center";
    modal.tabIndex = -1;

    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <button class="btn-close" data-bs-dismiss="modal"></button>
                    <div class="modal-title" id="image-modal-title"></div>
                </div>
                <div class="modal-body">
                    <a id="image-modal-link" target="_blank">
                        <img id="image-modal-img"
                             style="max-width:100%; max-height:70vh; width:auto; height:auto;">
                    </a>
                </div>
            </div>
        </div>`;
    
    document.body.appendChild(modal);

    const bsModal = new bootstrap.Modal(modal);
    const img = modal.querySelector("#image-modal-img");
    const linkEl = modal.querySelector("#image-modal-link");
    const titleEl = modal.querySelector("#image-modal-title");

    document.addEventListener("click", e => {
        if (e.target.closest("#image-modal")) return;

        const link = e.target.closest("a[href]");
        if (!link) return;

        const href = link.getAttribute("href");
        if (!/\.(gif|png|jpe?g|ico|webp)$/i.test(href)) return;
        if (link.dataset.bsToggle === "modal") return;
        if (!sanitizeUrl(href)) return;

        e.preventDefault();

        const innerImg = link.querySelector("img");
        const alt = innerImg?.alt || "";
        const title = innerImg?.title || "";

        let caption = alt && alt !== href ? alt :
                      title && title !== href ? title : "";

        caption = sanitizeHTML(caption.replace(/^Link to /i, ""));

        img.src = href;
        img.alt = caption;
        linkEl.href = href;
        titleEl.textContent = caption;

        bsModal.show();

        modal.addEventListener("hidden.bs.modal", () => link.focus(), {once:true});
    });

});