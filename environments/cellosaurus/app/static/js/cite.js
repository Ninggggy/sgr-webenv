document.addEventListener("DOMContentLoaded", function() {
    
    const DOI_BASE = "https://doi.org/";
    const PUBMED_BASE = "https://pubmed.ncbi.nlm.nih.gov/";
    const PMC_BASE = "https://www.ncbi.nlm.nih.gov/pmc/articles/";
    const NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/";
    
    /* Automatically add links to doi, pubmed and pmc */
    document.querySelectorAll(".reference").forEach(ref => {
        const doi = ref.dataset.doi?.trim();
        const pmid = ref.dataset.pmid?.trim();
        const pmcid = ref.dataset.pmcid?.trim();

        const title = ref.querySelector(".title");
        const linkContainer = ref.querySelector(".links");

        let titleHref = "";
        if (pmid) {
            titleHref = PUBMED_BASE + pmid + "/";
        } else if (doi) {
            titleHref = DOI_BASE + doi;
        } else if (pmcid) {
            titleHref = PMC_BASE + pmcid + "/";
        }

        if (title && titleHref && !title.querySelector("a")) {
            const a = document.createElement("a");
            a.href = titleHref;
            a.textContent = title.textContent.trim();
            a.target = "_blank";
            a.rel = "noopener noreferrer";
            title.textContent = "";
            title.appendChild(a);
        }

        const links = [];
        if (doi)
            links.push(`[<a href="${DOI_BASE}${doi}" target="_blank" rel="noopener noreferrer">doi</a>]`);

        if (pmid)
            links.push(`[<a href="${PUBMED_BASE}${pmid}/" target="_blank" rel="noopener noreferrer">pubmed</a>]`);

        if (pmcid)
            links.push(`[<a href="${PMC_BASE}${pmcid}/" target="_blank" rel="noopener noreferrer">pmc</a>]`);

        if (linkContainer) {
            linkContainer.innerHTML = links.join(" ");
        }
    });

    const citeButtons = document.querySelectorAll(".cite-btn");

    citeButtons.forEach((btn) => {
        btn.addEventListener("click", function() {
            const pmid = btn.dataset.pmid;
            if (!pmid) return;
            showModal(pmid);
        });
    });

    function showModal(pmid) {
        const overlay = document.createElement("div");
        overlay.className = "pm-modal-overlay";
        overlay.innerHTML = `
                <div class="pm-modal">
                    <div class="pm-modal-header">
                        <h3 class="pm-modal-title">CITE</h3>
                        <button class="pm-modal-close" type="button">&times;</button>
                    </div>
                    <div class="pm-modal-body">
                        <div class="pm-loading">Loading citation...</div>
                    </div>
                    <div class="pm-modal-footer" style="display:none">
                        <button class="pm-copy-btn" type="button">Copy</button>
                        <div>
                            <span style="font-size:12px; color:#666; margin-right:8px;">Format:</span>
                            <select class="pm-format-select">
                                <option value="NLM">NLM</option>
                                <option value="AMA">AMA</option>
                                <option value="APA">APA</option>
                                <option value="MLA">MLA</option>
                            </select>
                        </div>
                    </div>
                </div>
            `;

        document.body.appendChild(overlay);

        const closeModal = () => document.body.removeChild(overlay);

        const closeBtn = overlay.querySelector(".pm-modal-close");
        closeBtn.addEventListener("click", closeModal);

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeModal;
        });

        fetchCitation(overlay, pmid);
    }

    async function fetchCitation(overlay, pmid) {
        const body = overlay.querySelector(".pm-modal-body");
        const footer = overlay.querySelector(".pm-modal-footer");
        const copyBtn = overlay.querySelector(".pm-copy-btn");
        const formatSelect = overlay.querySelector(".pm-format-select");

        try {
            const res = await fetch(
                `${NCBI_EUTILS_BASE}/esummary.fcgi?db=pubmed&id=${pmid}&retmode=json`
            );
            const data = await res.json();
            const article = data.result[pmid];
            
            if (!article) {
                throw new Error("Article not found");
            }

            const formats = generateFormats(article, pmid);

            function updateDisplay() {
                const format = formatSelect.value;
                body.innerHTML = `<div class="pm-citation-box">${formats[format]}</div>`;
            }

            formatSelect.addEventListener("change", updateDisplay);

            copyBtn.addEventListener("click", () => {
                const text = body.querySelector(".pm-citation-box").innerText;
                navigator.clipboard.writeText(text).then(() => {
                    const originalText = copyBtn.innerText;
                    copyBtn.innerText = "Copied!";
                    setTimeout(() => {
                        copyBtn.innerText = originalText;
                    }, 2000);
                });
            });

            footer.style.display = "flex";
            updateDisplay();
        } catch (err) {
            body.innerHTML = `<div style="color:red; text-align:center">Error loading citation. Please check the PMID.</div>`;
        }
    }

    function generateFormats(a, pmid) {
        const authors = (a.authors || []).map((au) => au.name);
        const shortAuthorStr =
            authors.length > 3
                ? authors.slice(0, 3).join(", ") + ", et al"
                : authors.join(", ");
        const nlmAuthors = authors.join(", ");

        const title = (a.title || "").replace(/\.$/, "");
        const journal = a.source || "";
        const fullJournal = a.fulljournalname || journal;
        const year = (a.pubdate || "").split(" ")[0];
        const date = a.pubdate || "";
        const vol = a.volume || "";
        const issue = a.issue || "";
        const pages = a.pages || "";
        const epub = a.epubdate || "";
        
        let doi = null;
        for (const id of a.articleids) {
          if (id.idtype === "doi") {
            doi = id.value;
            break;
          }
        }
        
        let pmc = null;
        for (const id of a.articleids) {
          if (id.idtype === "pmc") {
            pmc = id.value;
            break;
          }
        }

        return {
            NLM: `${nlmAuthors}. ${title}. ${journal}. ${date};${vol}(${issue}):${pages}. ${doi ? "doi: " + doi + ". " : ""}${epub ? "Epub " + epub + ". " : ""}PMID: ${pmid}${pmc ? "; PMCID: " + pmc : ""}.`,
            AMA: `${shortAuthorStr}. ${title}. <i>${journal}</i>. ${year};${vol}(${issue}):${pages}.${doi ? " doi:" + doi : ""}`,
            APA: `${authors
                .map((n) => {
                    const parts = n.trim().split(/\s+/);
                    const initials = parts.pop() || "";
                    const surname = parts.join(" ");

                    return (
                        surname +
                        ", " +
                        initials.split("").join(". ") +
                        (initials ? "." : "")
                    );
                })
                .join(", ")} (${year}). ${title}. <i>${fullJournal}</i>, <i>${vol}</i>(${issue}), ${pages}.${doi ? " https://doi.org/" + doi : ""}`,
            MLA: `${authors[0] || ""}. "${title}." <i>${fullJournal}</i>, vol. ${vol}, no. ${issue}, ${year}, pp. ${pages}.${doi ? " doi:" + doi : ""}`,
        };
    }
});