

document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const caseInput = document.getElementById('caseNumberInput');
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileName');
    const evidenceList = document.getElementById('evidenceList');
    const analysisSection = document.getElementById('analysisSection');
    const analysisContent = document.getElementById('analysisContent');
    const analysisDocId = document.getElementById('analysisDocId');


    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameDisplay.textContent = fileInput.files[0].name;
        } else {
            fileNameDisplay.textContent = "";
        }
    });


    let timeout = null;
    caseInput.addEventListener('input', () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            if (caseInput.value.length > 3) {
                loadEvidence();
            }
        }, 800);
    });


    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const caseNumber = caseInput.value.trim();
        const file = fileInput.files[0];

        if (!caseNumber) {
            alert("Please enter a Case Number.");
            return;
        }
        if (!file) {
            alert("Please select a file.");
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('case_number', caseNumber);

        try {
            const btn = uploadForm.querySelector('button');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
            btn.disabled = true;

            const res = await fetch('/api/evidence/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {

                fileInput.value = "";
                fileNameDisplay.textContent = "";

                loadEvidence();
            } else {
                alert("Upload failed: " + data.error);
            }

            btn.innerHTML = originalText;
            btn.disabled = false;

        } catch (err) {
            console.error(err);
            alert("An error occurred during upload.");
        }
    });


    window.loadEvidence = async function () {
        const caseNumber = caseInput.value.trim();
        if (!caseNumber) return;

        evidenceList.innerHTML = '<div class="text-center text-gray-500 py-4"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';

        try {

            const res = await fetch(`/api/evidence/list?case_number=${encodeURIComponent(caseNumber)}`);
            const docs = await res.json();

            evidenceList.innerHTML = '';

            if (docs.length === 0) {
                evidenceList.innerHTML = '<div class="text-center text-gray-500 py-4">No documents found for this case.</div>';
                return;
            }

            docs.forEach(doc => {
                const item = document.createElement('div');
                item.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-white hover:shadow-sm transition-all';

                const hasAnalysis = !!doc.analysis;
                const dateC = new Date(doc.upload_date).toLocaleDateString();

                item.innerHTML = `
                    <div class="flex items-center gap-3 overflow-hidden">
                        <div class="flex flex-col items-center gap-1">
                            <div class="p-2 bg-indigo-50 text-indigo-600 rounded">
                                <i class="fas ${['jpg', 'jpeg', 'png', 'webp'].includes(doc.filename.split('.').pop().toLowerCase()) ? 'fa-image' : 'fa-file-alt'}"></i>
                            </div>
                            <!-- Hash Badge -->
                            <span class="text-[10px] bg-gray-100 text-gray-500 px-1 rounded font-mono" title="SHA-256 Hash">
                                ${doc.file_hash ? doc.file_hash.substring(0, 6) : 'PENDING'}...
                            </span>
                        </div>
                        <div class="min-w-0">
                            <p class="font-medium text-gray-800 text-sm truncate" title="${doc.filename}">${doc.filename}</p>
                            <p class="text-xs text-gray-500">${dateC}</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                         ${['jpg', 'jpeg', 'png', 'webp'].includes(doc.filename.split('.').pop().toLowerCase()) ?
                        `<span class="text-[9px] bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded font-bold uppercase tracking-tighter">Vision Scan</span>` : ''}
                         ${hasAnalysis ?
                        `<span class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Analyzed</span>` : ''}
                        
                         ${localStorage.getItem("role") === 'admin' ?
                        `<button onclick="deleteEvidence('${doc.id}')" class="text-sm px-3 py-1.5 bg-white border border-red-200 rounded text-red-600 hover:bg-red-50 hover:border-red-300 transition-colors" title="Delete Evidence">
                            <i class="fas fa-trash-alt"></i>
                         </button>` : ''}

                        <!-- Verify Button -->
                         <button onclick="verifyIntegrity('${doc.id}', this)" class="text-sm px-3 py-1.5 bg-white border border-gray-300 rounded text-gray-700 hover:bg-green-50 hover:text-green-600 hover:border-green-200 transition-colors" title="Verify Immutable Ledger">
                            <i class="fas fa-shield-alt"></i>
                        </button>

                        <button onclick="triggerAnalysis('${doc.id}')" class="text-sm px-3 py-1.5 bg-white border border-gray-300 rounded text-gray-700 hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200 transition-colors">
                            ${hasAnalysis ? 'View Analysis' : 'Analyze <i class="fas fa-magic text-yellow-500 ml-1"></i>'}
                        </button>
                    </div>
                `;
                evidenceList.appendChild(item);
            });

        } catch (err) {
            console.error(err);
            evidenceList.innerHTML = '<div class="text-center text-red-500 py-4">Failed to load documents.</div>';
        }
    };

    window.deleteEvidence = async function (id) {
        if (!confirm("Are you sure you want to permanently delete this evidence file?")) return;

        try {
            const res = await fetch(`/api/evidence/${id}`, { method: 'DELETE' });
            const data = await res.json();

            if (data.success) {
                // Refresh list
                loadEvidence();
            } else {
                alert("Delete failed: " + data.error);
            }
        } catch (e) {
            alert("Error deleting file.");
        }
    };


    window.triggerAnalysis = async function (docId) {
        analysisSection.classList.remove('hidden');
        analysisDocId.textContent = `ID: ${docId.substring(0, 8)}...`;





        analysisContent.innerHTML = `
            <div class="flex flex-col items-center justify-center py-8 text-gray-500 gap-3">
                <i class="fas fa-robot fa-spin text-3xl text-indigo-400"></i> 
                <p>AI is reading and analyzing the document...</p>
                <p class="text-xs text-gray-400">This runs locally on Ollama/Mistral and may take a few seconds.</p>
            </div>
        `;

        try {
            const res = await fetch('/api/evidence/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ evidence_id: docId })
            });
            const data = await res.json();

            if (data.success) {

                const formatted = data.analysis.replace(/\n/g, '<br>');
                analysisContent.innerHTML = `<div class="leading-relaxed whitespace-pre-line">${data.analysis}</div>`;


                loadEvidence();
            } else {
                analysisContent.innerHTML = `<div class="text-red-500">Analysis Failed: ${data.error}</div>`;
            }

        } catch (err) {
            analysisContent.innerHTML = `<div class="text-red-500">Network Error</div>`;
        }
    };


    window.verifyIntegrity = async function (docId, btn) {
        const originalIcon = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
        btn.disabled = true;

        try {
            const res = await fetch('/api/evidence/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ evidence_id: docId })
            });
            const data = await res.json();

            if (data.verified) {

                btn.className = "text-sm px-3 py-1.5 bg-green-100 border border-green-300 rounded text-green-700 transition-all";
                btn.innerHTML = '<i class="fas fa-check-circle"></i> Verified';
                btn.title = "Verified on Immutable Ledger";


            } else {

                btn.className = "text-sm px-3 py-1.5 bg-red-100 border border-red-300 rounded text-red-700 transition-all";
                btn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> TAMPERED';
                alert("SECURITY ALERT: " + data.message + "\nExpected: " + data.expected + "\nActual: " + data.actual);
            }
        } catch (err) {
            console.error(err);
            btn.innerHTML = '<i class="fas fa-times"></i> Err';
            alert("Network error during verification.");
        }
    };

});
