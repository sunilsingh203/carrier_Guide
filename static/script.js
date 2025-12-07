document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('career-form');
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const submitSpinner = document.getElementById('submit-spinner');
    const resultsSection = document.getElementById('results-section');
    const formSection = document.getElementById('form-section');
    const thinkingBlock = document.getElementById('thinking-block');
    
    // Helper function to escape HTML special characters
    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // Helper to format list items which might be strings or objects
    function formatListItem(item) {
        if (item === null || item === undefined) return '';
        if (typeof item === 'string') return item;
        if (typeof item === 'number' || typeof item === 'boolean') return String(item);
        // If it's an object, try common fields
        if (typeof item === 'object') {
            // Common fields for courses/resources/projects
            const keys = ['title', 'name', 'label', 'course', 'resource', 'description', 'url', 'link'];
            for (const k of keys) {
                if (item[k]) {
                    return String(item[k]);
                }
            }
            // If it has nested fields, try to stringify compactly
            try {
                // Prefer small readable output: combine first few keys
                const entries = Object.entries(item).slice(0, 4).map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`);
                return entries.join(' | ');
            } catch (e) {
                return JSON.stringify(item);
            }
        }
        return String(item);
    }

    // Helper to format timelines which may be arrays, objects with phases/milestones, or plain strings
    function formatTimeline(timeline) {
        if (!timeline) return '';
        // If it's a string or number
        if (typeof timeline === 'string' || typeof timeline === 'number') {
            return escapeHtml(String(timeline)).replace(/\n/g, '<br>');
        }

        // If it's an array
        if (Array.isArray(timeline)) {
            // Array may contain strings or objects
            return timeline.map((t, i) => {
                if (typeof t === 'string' || typeof t === 'number') return `- ${escapeHtml(String(t))}`;
                if (typeof t === 'object') {
                    // try common object patterns
                    const title = t.phase || t.title || t.name || t.milestone || t.step;
                    const when = t.duration || t.timeframe || t.when || t.timeline;
                    const desc = t.description || t.summary || t.details || '';
                    const parts = [];
                    if (title) parts.push(escapeHtml(String(title)));
                    if (when) parts.push(`<em class="text-gray-400">${escapeHtml(String(when))}</em>`);
                    if (desc) parts.push(escapeHtml(String(desc)));
                    return `- ${parts.join(' — ')}`;
                }
                return `- ${escapeHtml(formatListItem(t))}`;
            }).join('<br>');
        }

        // If it's an object
        if (typeof timeline === 'object') {
            // Common shapes: { phases: [...] } or { milestones: [...] }
            const arraysKeys = ['phases', 'milestones', 'steps', 'stages'];
            for (const k of arraysKeys) {
                if (Array.isArray(timeline[k])) {
                    return formatTimeline(timeline[k]);
                }
            }

            // If object is a map of label -> description
            const entries = Object.entries(timeline);
            // If many entries and values are strings, render as list
            if (entries.length > 0) {
                // If values are mostly strings or simple, render pairs
                const simple = entries.every(([k, v]) => typeof v === 'string' || typeof v === 'number');
                if (simple) {
                    return entries.map(([k, v]) => `- <strong>${escapeHtml(k)}:</strong> ${escapeHtml(String(v))}`).join('<br>');
                }

                // If entries contain nested objects/arrays, try to render each entry compactly
                return entries.map(([k, v]) => {
                    if (Array.isArray(v)) {
                        return `<strong>${escapeHtml(k)}:</strong><br>${formatTimeline(v)}`;
                    } else if (typeof v === 'object') {
                        const title = v.title || v.name || null;
                        const desc = v.description || v.summary || v.details || '';
                        return `- <strong>${escapeHtml(k)}${title ? ' — ' + escapeHtml(title) : ''}:</strong> ${escapeHtml(String(desc))}`;
                    } else {
                        return `- <strong>${escapeHtml(k)}:</strong> ${escapeHtml(String(v))}`;
                    }
                }).join('<br>');
            }

            // Fallback: stringify compactly
            try {
                return escapeHtml(JSON.stringify(timeline));
            } catch (e) {
                return escapeHtml(String(timeline));
            }
        }

        return escapeHtml(String(timeline));
    }

    // Add loading state to the button
    function setLoading(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtn.classList.add('opacity-75');
            submitText.textContent = 'Analyzing...';
            submitSpinner.classList.remove('hidden');
            thinkingBlock.classList.remove('hidden');
        } else {
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-75');
            submitText.textContent = 'Get Career Recommendations';
            submitSpinner.classList.add('hidden');
            thinkingBlock.classList.add('hidden');
        }
    }

    // Show error message
    function showError(message) {
        // Create or update error message element
        let errorDiv = document.getElementById('error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'error-message';
            errorDiv.className = 'mb-4 p-4 bg-red-900 border border-red-700 text-red-200 rounded-lg';
            form.insertBefore(errorDiv, form.firstChild);
        }
        errorDiv.textContent = message;
    }

    // Handle form submission
    async function handleSubmit(e) {
        e.preventDefault();
        
        try {
            // Reset any previous errors
            const errorDiv = document.getElementById('error-message');
            if (errorDiv) {
                errorDiv.remove();
            }

            // Show loading state
            setLoading(true);

            const formData = {
                skills: document.getElementById('skills').value,
                interests: document.getElementById('interests').value,
                strengths: document.getElementById('strengths').value,
                personality_traits: document.getElementById('personality_traits').value,
                work_style: document.getElementById('work_style').value,
                education: document.getElementById('education').value,
                salary_expectations: document.getElementById('salary_expectations').value,
                tech_preference: document.getElementById('tech_preference').value,
                learning_ability: document.getElementById('learning_ability').value,
                past_projects: document.getElementById('past_projects').value
            };

            console.log('Sending form data:', formData);

            // Make API request using relative URL
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            console.log('Response status:', response.status);

            const data = await response.json();
            console.log('Response data:', data);

            if (!response.ok) {
                throw new Error(data.message || data.error || 'Something went wrong');
            }

            // Show results
            showResults(data);

        } catch (error) {
            console.error('Error:', error);
            showError(error.message || 'An error occurred. Please try again.');
        } finally {
            setLoading(false);
        }
    }

    // Display results
    function showResults(data) {
        console.log('showResults called with data:', data);
        
        // Hide form and thinking block
        formSection.classList.add('hidden');
        thinkingBlock.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        
        // Build main results container with a dedicated list area and pagination controls
        resultsSection.innerHTML = `
            <div class="space-y-6">
                <div class="text-center mb-6">
                    <h2 class="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-600 mb-2">Your Career Roadmap</h2>
                    <p class="text-gray-400">Personalized career paths based on your profile</p>
                </div>

                <div id="results-main" class="max-w-6xl mx-auto bg-gray-800 rounded-2xl shadow-2xl border border-gray-700 p-6">
                    <div id="results-list" class="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-2"></div>
                    <div id="pagination-controls" class="mt-6 flex items-center justify-center gap-3"></div>
                </div>

                <div class="flex justify-center gap-4 mt-8 pt-6 border-t border-gray-700">
                    <button id="start-over-btn" class="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold rounded-lg hover:from-indigo-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 flex items-center gap-2">
                        <i class="fas fa-redo"></i> Start Over
                    </button>
                    <button id="print-btn" class="px-6 py-3 bg-gray-700 text-white font-bold rounded-lg hover:bg-gray-600 transition-all duration-300 transform hover:scale-105 flex items-center gap-2">
                        <i class="fas fa-print"></i> Print
                    </button>
                </div>
            </div>
        `;

        // Prepare cards for pagination
        const formatted = formatResults(data);
        if (Array.isArray(formatted)) {
            const cardsArray = formatted; // array of HTML strings
            const CARDS_PER_PAGE = 3;
            let currentPage = 1;
            const totalPages = Math.max(1, Math.ceil(cardsArray.length / CARDS_PER_PAGE));

            function renderPage(page) {
                currentPage = Math.min(Math.max(1, page), totalPages);
                const start = (currentPage - 1) * CARDS_PER_PAGE;
                const end = start + CARDS_PER_PAGE;
                const pageCards = cardsArray.slice(start, end);
                const resultsList = document.getElementById('results-list');
                resultsList.innerHTML = pageCards.join('');
                renderPagination();
                // smooth scroll to top of results
                document.getElementById('results-main').scrollIntoView({behavior: 'smooth', block: 'start'});
            }

            function renderPagination() {
                const container = document.getElementById('pagination-controls');
                container.innerHTML = '';

                // Prev button
                const prev = document.createElement('button');
                prev.className = 'px-3 py-2 bg-gray-700 text-gray-200 rounded-md hover:bg-gray-600';
                prev.textContent = 'Prev';
                prev.disabled = currentPage === 1;
                prev.onclick = () => renderPage(currentPage - 1);
                container.appendChild(prev);

                // page indicators
                const indicator = document.createElement('span');
                indicator.className = 'text-gray-300 px-4';
                indicator.textContent = `Page ${currentPage} of ${totalPages}`;
                container.appendChild(indicator);

                // Next button
                const next = document.createElement('button');
                next.className = 'px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-500';
                next.textContent = 'Next';
                next.disabled = currentPage === totalPages;
                next.onclick = () => renderPage(currentPage + 1);
                container.appendChild(next);
            }

            // Wire up utility buttons
            document.getElementById('start-over-btn').onclick = () => location.reload();
            document.getElementById('print-btn').onclick = () => window.print();

            // Initial render
            renderPage(1);
        } else {
            // Fallback: formatted is raw HTML string
            const resultsList = document.getElementById('results-list');
            resultsList.innerHTML = `<div class="p-6">${formatted}</div>`;
            document.getElementById('start-over-btn').onclick = () => location.reload();
            document.getElementById('print-btn').onclick = () => window.print();
        }
        
        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }

    // Format the results for display
    function formatResults(data) {
        try {
            console.log('formatResults data:', data);
            
            // Get the result output
            let result = data.result;
            
            console.log('Result type:', typeof result);
            console.log('Result value:', result);
            
            if (!result) {
                return `<div class="text-center text-gray-400 py-12"><p>No results available</p></div>`;
            }
            
                // If result is a string, try to extract JSON content and parse it
                if (typeof result === 'string') {
                    // Clean common wrappers: remove leading 'Thought:' text and code fences
                    let cleaned = result.trim();

                    // If contains ```json ... ``` or ``` ... ``` extract inner content
                    const fencedJsonMatch = cleaned.match(/```json\\s*([\\s\\S]*?)```/i);
                    const fencedMatch = cleaned.match(/```,\\s*([\\s\\S]*?)```/);
                    if (fencedJsonMatch && fencedJsonMatch[1]) {
                        cleaned = fencedJsonMatch[1].trim();
                    } else if (fencedMatch && fencedMatch[1]) {
                        cleaned = fencedMatch[1].trim();
                    } else {
                        // Remove any leading explanation up to first JSON bracket
                        const firstBrace = cleaned.indexOf('{');
                        const lastBrace = cleaned.lastIndexOf('}');
                        if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
                            cleaned = cleaned.substring(firstBrace, lastBrace + 1);
                        }
                    }

                    // Try parsing the cleaned content
                    try {
                        result = JSON.parse(cleaned);
                        console.log('Parsed JSON result after cleaning:', result);
                    } catch (e) {
                        console.warn('Could not parse as JSON after cleaning, treating as plain text');
                        return `<div class="bg-gray-800 rounded-2xl border border-gray-700 p-8">
                            <h3 class="text-xl font-semibold text-purple-400 mb-4">AI Recommendations:</h3>
                            <div class="text-gray-300 whitespace-pre-wrap text-sm max-h-96 overflow-y-auto">
                                ${escapeHtml(result)}
                            </div>
                        </div>`;
                    }
            }
            
            // If it's an object with career_roadmaps array
            if (typeof result === 'object' && result.career_roadmaps && Array.isArray(result.career_roadmaps)) {
                console.log('Found career_roadmaps array');
                return formatCareerRoadmaps(result.career_roadmaps);
            }
            
            // If it's an object with roadmap property (nested structure)
            if (typeof result === 'object' && result.roadmap) {
                console.log('Found roadmap property');
                const roadmapData = result.roadmap;
                if (Array.isArray(roadmapData)) {
                    return formatCareerRoadmaps(roadmapData);
                } else if (roadmapData.career_roadmaps && Array.isArray(roadmapData.career_roadmaps)) {
                    return formatCareerRoadmaps(roadmapData.career_roadmaps);
                }
            }
            
            // If it's an array directly
            if (Array.isArray(result)) {
                console.log('Result is array');
                // Check if it's an array of career objects
                if (result.length > 0 && (result[0].career_title || result[0].title)) {
                    return formatCareerRoadmaps(result);
                }
            }
            
            // If it's a plain object, format it nicely
            if (typeof result === 'object') {
                console.log('Result is plain object, converting to string');
                return `<div class="bg-gray-800 rounded-2xl border border-gray-700 p-8">
                    <h3 class="text-xl font-semibold text-purple-400 mb-4">AI Recommendations:</h3>
                    <pre class="text-gray-300 text-sm overflow-x-auto font-mono max-h-96 overflow-y-auto">${escapeHtml(JSON.stringify(result, null, 2))}</pre>
                </div>`;
            }
            
            return `<div class="text-center text-gray-400 py-12"><p>Unable to parse results</p></div>`;
        } catch (error) {
            console.error('Error formatting results:', error);
            return `<div class="bg-red-900 rounded-2xl border border-red-700 p-8">
                <p class="text-red-200 font-semibold"><i class="fas fa-exclamation-circle mr-2"></i>Error displaying results:</p>
                <p class="text-red-300 mt-2">${error.message}</p>
            </div>`;
        }
    }

    // Format career roadmaps into beautiful cards
    function formatCareerRoadmaps(roadmaps) {
        console.log('formatCareerRoadmaps called with:', roadmaps);

        if (!Array.isArray(roadmaps) || roadmaps.length === 0) {
            return [];
        }

        // Return an array of card HTML strings for pagination
        return roadmaps.map((career, index) => {
            const roadmap = career.roadmap || career;

            const title = career.career_title || roadmap.career_title || roadmap.title || `Career Path ${index + 1}`;
            const skills = roadmap.required_skills_to_learn || roadmap.required_skills || roadmap.skills || [];
            const courses = roadmap.recommended_courses_resources || roadmap.recommended_courses || roadmap.courses || [];
            const projects = roadmap.suggested_projects || roadmap.projects || [];
            const timeline = roadmap.timeline_for_skill_acquisition || roadmap.timeline || roadmap.phase_1_foundational_skills || '';
            const certifications = roadmap.certifications || roadmap.recommended_certifications || [];

            const parts = [];
            parts.push(`<div class="career-card fade-in visible" style="animation-delay: ${index * 0.06}s;">`);
            parts.push(`<div class="flex items-start justify-between mb-4">`);
            parts.push(`<div class="career-title flex-1"><i class="fas fa-briefcase mr-3"></i>${escapeHtml(title)}</div>`);
            parts.push(`<span class="bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-3 py-1 rounded-full text-sm font-semibold">Path ${index + 1}</span>`);
            parts.push(`</div>`);

            if (roadmap.summary) {
                parts.push(`<div class="text-gray-300 mb-3 text-sm">${escapeHtml(String(roadmap.summary))}</div>`);
            }

            if (skills && skills.length > 0) {
                parts.push(`<div class="section-heading"><i class="fas fa-star"></i> Skills</div>`);
                parts.push(`<div class="flex flex-wrap gap-2 mb-3">`);
                parts.push(skills.map(skill => `<div class="skill-item inline-block px-3 py-2">${escapeHtml(formatListItem(skill))}</div>`).join(''));
                parts.push(`</div>`);
            }

            if (courses && courses.length > 0) {
                parts.push(`<div class="section-heading"><i class="fas fa-book"></i> Courses</div>`);
                parts.push(`<div class="space-y-2 mb-3">`);
                parts.push(courses.slice(0,3).map(r => `<div class="resource-item">${escapeHtml(formatListItem(r))}</div>`).join(''));
                if (courses.length > 3) parts.push(`<div class="text-gray-400 text-sm">+ ${courses.length - 3} more resources</div>`);
                parts.push(`</div>`);
            }

            if (projects && projects.length > 0) {
                parts.push(`<div class="section-heading"><i class="fas fa-project-diagram"></i> Projects</div>`);
                parts.push(`<div class="space-y-2 mb-3">`);
                parts.push(projects.slice(0,2).map((p, idx) => `<div class="project-item"><strong>Project ${idx + 1}:</strong> ${escapeHtml(formatListItem(p))}</div>`).join(''));
                if (projects.length > 2) parts.push(`<div class="text-gray-400 text-sm">+ ${projects.length - 2} more project ideas</div>`);
                parts.push(`</div>`);
            }

            if (timeline) {
                parts.push(`<div class="section-heading"><i class="fas fa-clock"></i> Timeline</div>`);
                let timelineHtml = '';
                if (Array.isArray(timeline)) {
                    timelineHtml = timeline.map(t => escapeHtml(formatListItem(t))).join('<br>');
                } else if (typeof timeline === 'object') {
                    timelineHtml = escapeHtml(formatListItem(timeline)).replace(/\n/g, '<br>');
                } else {
                    timelineHtml = escapeHtml(String(timeline)).replace(/\n/g, '<br>');
                }
                parts.push(`<div class="timeline-content mb-3">${timelineHtml}</div>`);
            }

            if (certifications && certifications.length > 0) {
                parts.push(`<div class="section-heading"><i class="fas fa-certificate"></i> Certifications</div>`);
                parts.push(`<div class="grid grid-cols-2 gap-2 mb-2">${certifications.slice(0,4).map(cert => `<div class="certification-item">${escapeHtml(formatListItem(cert))}</div>`).join('')}</div>`);
            }

            parts.push(`</div>`);
            return parts.join('');
        });
    }

    // Helper function to escape HTML special characters
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // Add event listener
    form.addEventListener('submit', handleSubmit);
});
