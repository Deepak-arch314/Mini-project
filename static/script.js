document.addEventListener("DOMContentLoaded", () => {
    // Input elements
    const originalInput = document.getElementById("original");
    const submittedInput = document.getElementById("submitted");
    const origCount = document.getElementById("original-count");
    const subCount = document.getElementById("submitted-count");

    // File buttons
    const origFile = document.getElementById("original-file");
    const subFile = document.getElementById("submitted-file");

    // Control buttons
    const sampleBtn = document.getElementById("sample-btn");
    const clearBtn = document.getElementById("clear-btn");
    const checkBtn = document.getElementById("check-btn");

    // Options & Results
    const algorithmSelect = document.getElementById("algorithm");
    const minWordsInput = document.getElementById("min-words");
    const resultsSection = document.getElementById("results");
    const errorBox = document.getElementById("error-box");

    // Highlight & Matches display boxes
    const matchesBox = document.getElementById("matches");
    const hlOriginal = document.getElementById("hl-original");
    const hlSubmitted = document.getElementById("hl-submitted");

    // Sample Data
    const sampleOriginal = `String matching algorithms are fundamental tools in computer science used to find occurrences of a pattern within a main text. Algorithms like Knuth-Morris-Pratt and Rabin-Karp optimize this process by avoiding unnecessary character comparisons.`;
    const sampleSubmitted = `String matching algorithms are basic tools in computer science used to find occurrences of a pattern within text. Algorithms like Knuth-Morris-Pratt optimize this process by avoiding unnecessary character comparisons.`;

    // 1. Live Word Counting
    function updateWordCounts() {
        if (originalInput && origCount) {
            const words = originalInput.value.trim() ? originalInput.value.trim().split(/\s+/).length : 0;
            origCount.textContent = `${words} words`;
        }
        if (submittedInput && subCount) {
            const words = submittedInput.value.trim() ? submittedInput.value.trim().split(/\s+/).length : 0;
            subCount.textContent = `${words} words`;
        }
    }

    if (originalInput) originalInput.addEventListener("input", updateWordCounts);
    if (submittedInput) submittedInput.addEventListener("input", updateWordCounts);

    // 2. Load Sample Button
    if (sampleBtn) {
        sampleBtn.addEventListener("click", () => {
            if (originalInput) originalInput.value = sampleOriginal;
            if (submittedInput) submittedInput.value = sampleSubmitted;
            updateWordCounts();
        });
    }

    // 3. Clear Button
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            if (originalInput) originalInput.value = "";
            if (submittedInput) submittedInput.value = "";
            if (resultsSection) resultsSection.hidden = true;
            if (errorBox) errorBox.hidden = true;
            updateWordCounts();
        });
    }

    // 4. File Upload Handlers
    function handleFileUpload(fileInput, targetTextarea) {
        if (!fileInput || !targetTextarea) return;
        fileInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (event) => {
                targetTextarea.value = event.target.result;
                updateWordCounts();
            };
            reader.readAsText(file);
        });
    }
    handleFileUpload(origFile, originalInput);
    handleFileUpload(subFile, submittedInput);

    // Helper: Escapes raw HTML strings safely
    function escapeHtml(text) {
        return text.replace(/[&<>"']/g, (m) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
        }[m]));
    }

    // Helper: Build highlighted HTML string from text matches
    function highlightText(fullText, matches, isOriginal) {
        if (!matches || !matches.length) return escapeHtml(fullText);

        let intervals = matches.map(m => isOriginal ? [m.orig_start, m.orig_end] : [m.sub_start, m.sub_end])
                               .filter(range => range[0] !== undefined && range[1] !== undefined)
                               .sort((a, b) => a[0] - b[0]);

        if (!intervals.length) return escapeHtml(fullText);

        let merged = [intervals[0]];
        for (let i = 1; i < intervals.length; i++) {
            let last = merged[merged.length - 1];
            if (intervals[i][0] <= last[1]) {
                last[1] = Math.max(last[1], intervals[i][1]);
            } else {
                merged.push(intervals[i]);
            }
        }

        let html = '';
        let lastIndex = 0;
        merged.forEach(([start, end]) => {
            html += escapeHtml(fullText.slice(lastIndex, start));
            html += `<mark class="highlight">${escapeHtml(fullText.slice(start, end))}</mark>`;
            lastIndex = end;
        });
        html += escapeHtml(fullText.slice(lastIndex));

        return html;
    }

    // 5. Check Plagiarism Button
    if (checkBtn) {
        checkBtn.addEventListener("click", async () => {
            if (errorBox) errorBox.hidden = true;

            const original = originalInput?.value || "";
            const submitted = submittedInput?.value || "";
            const algorithm = algorithmSelect?.value || "ngram";
            const minWords = parseInt(minWordsInput?.value || "4");

            if (!original.trim() || !submitted.trim()) {
                if (errorBox) {
                    errorBox.textContent = "Please provide both original and submitted text.";
                    errorBox.hidden = false;
                } else {
                    alert("Please provide both original and submitted text.");
                }
                return;
            }

            try {
                const response = await fetch("/check", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        original: original,
                        submitted: submitted,
                        algorithm: algorithm,
                        min_words: minWords
                    })
                });

                const data = await response.json();

                if (!response.ok || data.error) {
                    if (errorBox) {
                        errorBox.textContent = data.error || "An error occurred during checking.";
                        errorBox.hidden = false;
                    }
                    return;
                }

                // Render Results
                if (resultsSection) {
                    resultsSection.hidden = false;
                    document.getElementById("score-value").textContent = `${data.similarity || 0}%`;
                    document.getElementById("meter-fill").style.width = `${data.similarity || 0}%`;
                    document.getElementById("verdict-text").textContent = (data.similarity || 0) > 30 ? "Plagiarism Detected" : "Low Similarity";
                    document.getElementById("verdict-sub").textContent = `Algorithm: ${algorithm.toUpperCase()}`;
                    
                    document.getElementById("st-orig").textContent = original.trim().split(/\s+/).length;
                    document.getElementById("st-sub").textContent = submitted.trim().split(/\s+/).length;
                    
                    // Matched words count calculation
                    const totalMatched = data.matched_words || data.matched_words_count || data.total_matched_words || 
                        (data.matches ? data.matches.reduce((sum, m) => sum + (m.word_count || m.length || 0), 0) : 0);
                    document.getElementById("st-match").textContent = totalMatched;
                    document.getElementById("st-sections").textContent = data.matches ? data.matches.length : 0;

                    // Render Matching Sections list
                    if (matchesBox) {
                        if (data.matches && data.matches.length) {
                            matchesBox.innerHTML = data.matches.map((m, idx) => `
                                <div class="match-item">
                                    <strong>Match #${idx + 1} (${m.word_count || m.length || 'N/A'} words):</strong>
                                    <p class="match-text">"${escapeHtml(m.text || m.matched_text || '')}"</p>
                                </div>
                            `).join('');
                        } else {
                            matchesBox.innerHTML = '<p>No matching sections found.</p>';
                        }
                    }

                    // Render Highlighted Comparison boxes
                    if (hlOriginal) {
                        hlOriginal.innerHTML = highlightText(original, data.matches, true);
                    }
                    if (hlSubmitted) {
                        hlSubmitted.innerHTML = highlightText(submitted, data.matches, false);
                    }
                }
            } catch (err) {
                console.error("Fetch error:", err);
                if (errorBox) {
                    errorBox.textContent = "Could not connect to the backend server.";
                    errorBox.hidden = false;
                }
            }
        });
    }

    // Initial word count calculation
    updateWordCounts();
});
