class CropRecommendationApp {
    constructor() {
        this.currentSection = 'home';
        this.downloadFileName = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadThemePreference();
        this.validateCropSelection();
    }

    setupEventListeners() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(link.dataset.section);
            });
        });

        document.getElementById('themeToggle').addEventListener('click', () => {
            this.toggleTheme();
        });


        document.getElementById('customCrop').addEventListener('input', (e) => {
            this.handleCropInput(e.target.value);
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.input-group')) {
                document.getElementById('suggestions').style.display = 'none';
            }
        });

        document.getElementById('cropForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCropRecommendation();
        });

        document.getElementById('compareForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCropComparison();
        });

        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.downloadRecommendations();
        });

        document.getElementById('printBtn').addEventListener('click', () => {
            this.printRecommendations();
        });

        document.querySelectorAll('input[name="crops"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.validateCropSelection());
        });
        document.getElementById('customCompareCrops').addEventListener('input', () => this.validateCropSelection());
    }

    switchSection(sectionName) {
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
        this.currentSection = sectionName;
    }


    async handleCropInput(fullQuery) {
        const queryParts = fullQuery.split(',');
        const currentTerm = queryParts[queryParts.length - 1].trim();

        if (currentTerm.length < 2) {
            document.getElementById('suggestions').style.display = 'none';
            return;
        }
        try {
            const response = await fetch('/suggest_crops', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: currentTerm })
            });
            const data = await response.json();
            this.displaySuggestions(data.suggestions);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
        }
    }


    displaySuggestions(suggestions) {
        const dropdown = document.getElementById('suggestions');
        if (suggestions.length === 0) {
            dropdown.style.display = 'none';
            return;
        }
        dropdown.innerHTML = suggestions.map(suggestion => `
                <div class="suggestion-item" onclick="app.selectSuggestion('${suggestion.crop.replace(/'/g, "\\'")}')">
                    <div class="suggestion-crop">${suggestion.crop}</div>
                    <div class="suggestion-category">${suggestion.category}</div>
                </div>
            `).join('');
        dropdown.style.display = 'block';
    }


    selectSuggestion(selectedCrop) {
        const input = document.getElementById('customCrop');
        const fullQuery = input.value;

        const queryParts = fullQuery.split(',');

        queryParts[queryParts.length - 1] = selectedCrop;

        input.value = queryParts.join(', ') + ', ';

        document.getElementById('suggestions').style.display = 'none';
        input.focus();
    }

    toggleTheme() {
        const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        document.getElementById('themeToggle').className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }

    loadThemePreference() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.getElementById('themeToggle').className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }

    async handleCropRecommendation() {
        const formData = {
            place: document.getElementById('place').value.trim(),
            category: document.getElementById('category').value,
            season: document.getElementById('season').value,
            custom_crop: document.getElementById('customCrop').value.trim()
        };

        if (!formData.place) {
            this.showToast('Please enter a location', 'error');
            return;
        }

        this.showLoading(true);
        this.switchSection('recommendations');

        try {
            const response = await fetch('/get_crop_recommendation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            document.getElementById('recommendations-content').innerHTML = data.recommendations;
            this.updateWeatherDisplay(data.weather);
            this.downloadFileName = data.download_file;
            document.getElementById('downloadBtn').style.display = 'inline-flex';
            document.getElementById('printBtn').style.display = 'inline-flex';
            this.showToast('Recommendations generated successfully!', 'success');
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('recommendations-content').innerHTML =
                '<div class="no-data"><i class="fas fa-exclamation-triangle"></i><h3>Error</h3><p>Failed to fetch recommendations. Please try again.</p></div>';
            this.showToast('Failed to generate recommendations', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    _getCombinedCrops() {
        const checkedCrops = Array.from(document.querySelectorAll('input[name="crops"]:checked'))
            .map(checkbox => checkbox.value);

        const customCropsText = document.getElementById('customCompareCrops').value.trim();
        const customCrops = customCropsText ? customCropsText.split(',')
            .map(crop => crop.trim())
            .filter(crop => crop) : [];

        const allCrops = [...checkedCrops, ...customCrops];
        return [...new Set(allCrops)];
    }

    async handleCropComparison() {
        const place = document.getElementById('comparePlace').value.trim();
        const uniqueCrops = this._getCombinedCrops();

        if (!place) {
            this.showToast('Please enter a location for comparison', 'error');
            return;
        }

        if (uniqueCrops.length < 2 || uniqueCrops.length > 5) {
            this.showToast('Please select a total of 2 to 5 crops to compare', 'error');
            return;
        }

        this.showComparisonLoading(true);

        try {
            const response = await fetch('/compare_crops', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ place: place, crops: uniqueCrops })
            });

            if (!response.ok) { throw new Error(`HTTP error! status: ${response.status}`); }

            const data = await response.json();
            document.getElementById('comparison-results').innerHTML = data.comparison;
            this.showToast('Crop comparison completed!', 'success');
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('comparison-results').innerHTML =
                '<div class="no-data"><i class="fas fa-exclamation-triangle"></i><h3>Comparison Failed</h3><p>Unable to compare crops. Please try again.</p></div>';
            this.showToast('Failed to compare crops', 'error');
        } finally {
            this.showComparisonLoading(false);
        }
    }

    validateCropSelection() {
        const uniqueCrops = this._getCombinedCrops();
        const count = uniqueCrops.length;
        const submitBtn = document.querySelector('#compareForm .search-btn');

        if (count < 2) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<i class="fas fa-balance-scale"></i> Select ${2 - count} more crop(s)`;
        } else if (count > 5) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<i class="fas fa-balance-scale"></i> Too many (${count}/5 selected)`;
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fas fa-balance-scale"></i> Compare ${count} Crop(s)`;
        }
    }

    updateWeatherDisplay(weather) {
        if (weather) {
            document.getElementById('temperature').textContent = weather.temperature;
            document.getElementById('humidity').textContent = weather.humidity;
            document.getElementById('rainfall').textContent = weather.rainfall;
            document.getElementById('currentSeason').textContent = weather.season;
            document.getElementById('weatherInfo').style.display = 'block';
        }
    }

    showLoading(show) {
        const spinner = document.getElementById('loadingSpinner');
        const content = document.getElementById('recommendations-content');
        if (show) {
            spinner.style.display = 'block';
            content.style.display = 'none';
        } else {
            spinner.style.display = 'none';
            content.style.display = 'block';
        }
    }

    showComparisonLoading(show) {
        const results = document.getElementById('comparison-results');
        if (show) {
            results.innerHTML = `
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <p>Comparing crops and analyzing market data...</p>
                    </div>`;
        }
    }

    downloadRecommendations() {
        if (this.downloadFileName) {
            window.open(`/download/${this.downloadFileName}`, '_blank');
            this.showToast('Download started!', 'info');
        } else {
            this.showToast('No recommendations to download', 'warning');
        }
    }

    printRecommendations() {
        const content = document.getElementById('recommendations-content').innerHTML;
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Crop Recommendations</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .crop-card { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
                        .crop-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 10px; color: #2c5530; background: #f8d825; padding: 0.5rem; border-radius: 4px; }
                        .section-header-detail { font-weight: bold; margin: 10px 0 5px 0; border-left: 3px solid #4a7c59; padding-left: 0.5rem; }
                        .detail-item { margin: 5px 0 5px 15px; }
                        .detail-key { font-weight: bold; }
                        @media print { body { margin: 0; } }
                    </style>
                </head>
                <body>
                    <h1>Crop Recommendations Report</h1>
                    <p>Generated on: ${new Date().toLocaleDateString()}</p>
                    ${content}
                </body>
                </html>`);
        printWindow.document.close();
        printWindow.print();
        this.showToast('Print dialog opened!', 'info');
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const icon = toast.querySelector('.toast-icon');
        const messageEl = toast.querySelector('.toast-message');

        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        icon.className = `toast-icon ${icons[type]}`;
        messageEl.textContent = message;
        toast.className = `toast ${type}`;
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
        }, 5000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new CropRecommendationApp();
});

class CustomDropdownHandler {
    constructor() {
        this.init();
    }

    init() {
        document.querySelectorAll('.custom-dropdown').forEach(dropdownElement => {
            this.setupDropdown(dropdownElement);
        });

        document.addEventListener('click', (e) => {
            document.querySelectorAll('.custom-dropdown.open').forEach(openDropdown => {
                if (!openDropdown.contains(e.target)) {
                    this.closeDropdown(openDropdown);
                }
            });
        });
    }

    setupDropdown(dropdownElement) {
        const trigger = dropdownElement.querySelector('.dropdown-trigger');
        const menu = dropdownElement.querySelector('.dropdown-menu');
        const options = menu.querySelectorAll('li');
        const hiddenInputId = dropdownElement.dataset.targetInput;
        const hiddenInput = document.getElementById(hiddenInputId);
        const selectedDisplay = trigger.querySelector('span');

        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            if (dropdownElement.classList.contains('open')) {
                this.closeDropdown(dropdownElement);
            } else {
                document.querySelectorAll('.custom-dropdown.open').forEach(openDropdown => this.closeDropdown(openDropdown));
                this.openDropdown(dropdownElement);
            }
        });

        options.forEach(option => {
            option.addEventListener('click', () => {
                hiddenInput.value = option.dataset.value;

                selectedDisplay.textContent = option.textContent;

                menu.querySelector('.selected')?.classList.remove('selected');
                option.classList.add('selected');

                this.closeDropdown(dropdownElement);
            });
        });
    }

    openDropdown(dropdownElement) {
        dropdownElement.classList.add('open');
    }

    closeDropdown(dropdownElement) {
        dropdownElement.classList.remove('open');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new CustomDropdownHandler();
});