/**
 * Pakistani News Relevance Dashboard - Application Logic
 * Implements interactive search, filters, charts, pagination, and theme toggle.
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
  const statsSection = document.getElementById("stats-section");
  const analyticsSection = document.getElementById("analytics-section");
  const tableCard = document.getElementById("table-card");
  const errorCard = document.getElementById("error-card");

  // Skeletons
  const loadingKpis = document.getElementById("loading-kpis");
  const loadingCharts = document.getElementById("loading-charts");
  const loadingTable = document.getElementById("loading-table");

  // Controls
  const statusTogglePill = document.getElementById("status-toggle-pill");
  const statusText = document.getElementById("status-text");
  const btnRefresh = document.getElementById("btn-refresh");
  const btnThemeToggle = document.getElementById("btn-theme-toggle");
  const btnErrorRetry = document.getElementById("btn-error-retry");

  // Filters
  const filterSearch = document.getElementById("filter-search");
  const filterMatchLevel = document.getElementById("filter-match-level");
  const filterMinRelevance = document.getElementById("filter-min-relevance");
  const relevanceSliderVal = document.getElementById("relevance-slider-val");
  const filterSort = document.getElementById("filter-sort");
  const btnResetFilters = document.getElementById("btn-reset-filters");

  // Table & Pagination
  const matchesTableBody = document.getElementById("matches-table-body");
  const resultsCount = document.getElementById("results-count");
  const paginationInfo = document.getElementById("pagination-info");
  const btnPrevPage = document.getElementById("btn-prev-page");
  const btnNextPage = document.getElementById("btn-next-page");

  // Table Sort Headers
  const thTextSim = document.getElementById("th-text-sim");
  const thImageSim = document.getElementById("th-image-sim");
  const thOverall = document.getElementById("th-overall");

  // --- State Variables ---
  let allMatches = []; // Loaded from window.MOCK_MATCHES
  let filteredMatches = [];
  let dashboardStats = {};
  let currentPage = 1;
  const rowsPerPage = 5;

  let isOnline = true;
  let isDarkMode = false;

  // Sorting state for table headers
  let activeHeaderSort = {
    field: null, // 'textSimilarity', 'imageSimilarity', 'overallScore'
    order: 'desc'
  };

  // Chart instances
  let pieChartInstance = null;
  let barChartInstance = null;

  // --- Initialization ---
  // FastAPI backend runs on port 8000; frontend static server on port 5500.
  // CORS is open (*) on the backend so hostname mismatches don't matter.
  const BACKEND_BASE_URL = window.BACKEND_BASE_URL || "http://127.0.0.1:8000";

  function escapeHTML(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function init() {
    // Check local storage or system preference for dark mode
    if (localStorage.getItem("theme") === "dark" ||
      (!localStorage.getItem("theme") && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      enableDarkMode();
    } else {
      disableDarkMode();
    }

    // Bind Event Listeners
    bindEvents();

    // Initialize interactive particle flow background
    initParticleBackground();

    // Initialize 3D tilt effects on cards
    initTiltCards();

    // Initial Fetch
    fetchData();
  }

  // --- Event Binding ---
  function bindEvents() {
    // Theme Toggle Click
    btnThemeToggle.addEventListener("click", toggleTheme);

    // Status Toggle (Online/Offline) Click
    statusTogglePill.addEventListener("click", () => {
      toggleBackendStatus();
    });

    // Retry button in error screen
    btnErrorRetry.addEventListener("click", () => {
      toggleBackendStatus(true);
    });

    // Refresh Button Click
    btnRefresh.addEventListener("click", () => {
      fetchData();
    });

    // Search input (debounce for search performance)
    let searchTimeout;
    filterSearch.addEventListener("input", () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        currentPage = 1;
        applyFiltersAndRender();
      }, 300);
    });

    // Dropdowns changes
    filterMatchLevel.addEventListener("change", () => {
      currentPage = 1;
      applyFiltersAndRender();
    });

    filterSort.addEventListener("change", () => {
      currentPage = 1;
      // Reset active header sorts when using dropdown sorting
      activeHeaderSort = { field: null, order: 'desc' };
      resetHeaderIcons();
      applyFiltersAndRender();
    });

    // Relevance slider change & update label
    filterMinRelevance.addEventListener("input", (e) => {
      relevanceSliderVal.textContent = `${e.target.value}%`;
      currentPage = 1;
      applyFiltersAndRender();
    });

    // Reset Filters button
    btnResetFilters.addEventListener("click", resetFilters);

    // Pagination Click
    btnPrevPage.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        renderPaginatedTable();
      }
    });

    btnNextPage.addEventListener("click", () => {
      const maxPages = Math.ceil(filteredMatches.length / rowsPerPage);
      if (currentPage < maxPages) {
        currentPage++;
        renderPaginatedTable();
      }
    });

    // Sortable Headers Click
    thTextSim.addEventListener("click", () => handleHeaderSort("textSimilarity", thTextSim));
    thImageSim.addEventListener("click", () => handleHeaderSort("imageSimilarity", thImageSim));
    thOverall.addEventListener("click", () => handleHeaderSort("overallScore", thOverall));

    // Relevance Calculator
    document.getElementById("btn-calc-relevance").addEventListener("click", computeRelevance);
  }

  // --- Theme Controls ---
  function toggleTheme() {
    if (document.body.classList.contains("dark-theme")) {
      disableDarkMode();
    } else {
      enableDarkMode();
    }
    // Update charts to match current mode
    if (isOnline) {
      initCharts();
    }
  }

  function enableDarkMode() {
    document.body.classList.add("dark-theme");
    localStorage.setItem("theme", "dark");
    isDarkMode = true;
    const container = document.getElementById("theme-icon-container");
    if (container) {
      container.innerHTML = `<i data-lucide="sun" style="width: 18px; height: 18px;"></i>`;
    }
    lucide.createIcons();
  }

  function disableDarkMode() {
    document.body.classList.remove("dark-theme");
    localStorage.setItem("theme", "light");
    isDarkMode = false;
    const container = document.getElementById("theme-icon-container");
    if (container) {
      container.innerHTML = `<i data-lucide="moon" style="width: 18px; height: 18px;"></i>`;
    }
    lucide.createIcons();
  }

  // --- Backend Status Sim ---
  function toggleBackendStatus(forceOnline = false) {
    if (forceOnline) {
      isOnline = true;
    } else {
      isOnline = !isOnline;
    }

    if (isOnline) {
      statusTogglePill.className = "status-pill online";
      statusText.textContent = "Backend: Online";
      fetchData();
    } else {
      statusTogglePill.className = "status-pill offline";
      statusText.textContent = "Backend: Offline";
      // Instantly trigger skeleton loading then show error
      fetchData();
    }
    lucide.createIcons();
  }

  // --- Fetching from Backend ---
  async function fetchData() {
    // Hide UI blocks, show skeletons
    toggleUIVisibility(true);

    // Keep the existing simulated delay for UX
    setTimeout(async () => {
      if (!isOnline) {
        // Show connection error screen, hide skeletons
        hideAllSkeletons();
        statsSection.classList.add("hidden");
        analyticsSection.classList.add("hidden");
        tableCard.classList.add("hidden");
        errorCard.classList.remove("hidden");
        return;
      }

      try {
        // Fetch matches + statistics in parallel
        const [matchesRes, statsRes] = await Promise.all([
          fetch(`${BACKEND_BASE_URL}/matches/`),
          fetch(`${BACKEND_BASE_URL}/statistics/`)
        ]);

        if (!matchesRes.ok) throw new Error(`Matches request failed: ${matchesRes.status}`);
        if (!statsRes.ok) throw new Error(`Statistics request failed: ${statsRes.status}`);

        const matchesJson = await matchesRes.json();
        const statsJson = await statsRes.json();

        // Map backend fields to frontend UI model
        allMatches = (matchesJson || []).map(m => ({
          id: m.dawn_id, // not used by UI, but kept for stability
          category: m.category || "General",
          dawnHeadline: m.dawn_headline,
          // Prefix backend-relative /images/ paths with the API base URL
          dawnImage: m.dawn_image
            ? (m.dawn_image.startsWith('http') ? m.dawn_image : `${BACKEND_BASE_URL}${m.dawn_image}`)
            : null,
          ummatHeadline: m.ummat_headline,
          ummatImage: m.ummat_image
            ? (m.ummat_image.startsWith('http') ? m.ummat_image : `${BACKEND_BASE_URL}${m.ummat_image}`)
            : null,
          textSimilarity: Math.round((m.text_similarity ?? 0) * (m.text_similarity <= 1 ? 100 : 1)),
          imageSimilarity: Math.round((m.image_similarity ?? 0) * (m.image_similarity <= 1 ? 100 : 1)),
          overallScore: Math.round((m.relevance_score ?? 0) * (m.relevance_score <= 1 ? 100 : 1)),
          matchLevel: m.match_level,
          publishDate: m.publishDate || null
        }));

        dashboardStats = statsJson;
        applyStatistics(statsJson);

        // Show normal UI, hide skeletons
        toggleUIVisibility(false);
        errorCard.classList.add("hidden");

        // Apply filter list
        currentPage = 1;
        applyFiltersAndRender();
      } catch (err) {
        // Show connection error screen
        console.error("Dashboard fetch error:", err);

        hideAllSkeletons();
        statsSection.classList.add("hidden");
        analyticsSection.classList.add("hidden");
        tableCard.classList.add("hidden");
        errorCard.classList.remove("hidden");
      }
    }, 900);
  }

  function applyStatistics(statsJson) {
    // The UI has two KPI modes:
    // - server-wide stats (this function)
    // - filter-derived stats (updateKPIs)
    // updateKPIs runs after applyFiltersAndRender and will overwrite
    // the match-level KPIs, so we only set the static totals here.

    document.getElementById("val-total-articles").textContent = statsJson?.total_articles ?? "-";
    document.getElementById("val-dawn-articles").textContent = statsJson?.dawn_articles ?? "-";
    document.getElementById("val-ummat-articles").textContent = statsJson?.ummat_articles ?? "-";

    document.getElementById("val-total-matches").textContent = statsJson?.total_matches ?? "-";
  }

  function toggleUIVisibility(isLoading) {
    if (isLoading) {
      // Skeletons: ON
      loadingKpis.classList.remove("hidden");
      loadingCharts.classList.remove("hidden");
      loadingTable.classList.remove("hidden");

      // Main UI: OFF
      statsSection.classList.add("hidden");
      analyticsSection.classList.add("hidden");
      tableCard.classList.add("hidden");
      errorCard.classList.add("hidden");
    } else {
      // Skeletons: OFF
      hideAllSkeletons();

      // Main UI: ON
      statsSection.classList.remove("hidden");
      analyticsSection.classList.remove("hidden");
      tableCard.classList.remove("hidden");
    }
  }

  function hideAllSkeletons() {
    loadingKpis.classList.add("hidden");
    loadingCharts.classList.add("hidden");
    loadingTable.classList.add("hidden");
  }

  // --- Filters, Sorting & Aggregation ---
  function applyFiltersAndRender() {
    const query = filterSearch.value.toLowerCase().trim();
    const matchLevel = filterMatchLevel.value;
    const minRelevance = parseInt(filterMinRelevance.value, 10);
    const sortVal = filterSort.value;

    // Filter
    filteredMatches = allMatches.filter(item => {
      const cat = item.category || "";
      const matchesQuery = !query ||
        (item.dawnHeadline || "").toLowerCase().includes(query) ||
        (item.ummatHeadline || "").toLowerCase().includes(query) ||
        cat.toLowerCase().includes(query);

      const matchesLevel = matchLevel === "All" || item.matchLevel === matchLevel;
      const matchesRelevance = item.overallScore >= minRelevance;

      return matchesQuery && matchesLevel && matchesRelevance;
    });

    // Sorting Logic
    if (activeHeaderSort.field) {
      // Clicked sorting headers directly
      filteredMatches.sort((a, b) => {
        let valA = a[activeHeaderSort.field];
        let valB = b[activeHeaderSort.field];
        return activeHeaderSort.order === 'asc' ? valA - valB : valB - valA;
      });
    } else {
      // Sidebar sorting dropdown
      if (sortVal === "highest") {
        filteredMatches.sort((a, b) => b.overallScore - a.overallScore);
      } else if (sortVal === "lowest") {
        filteredMatches.sort((a, b) => a.overallScore - b.overallScore);
      } else if (sortVal === "newest") {
        // Backend match response does not include publishDate.
        // Fall back to relevance score sorting.
        filteredMatches.sort((a, b) => b.overallScore - a.overallScore);
      } else if (sortVal === "oldest") {
        // Backend match response does not include publishDate.
        // Fall back to relevance score sorting.
        filteredMatches.sort((a, b) => a.overallScore - b.overallScore);
      }
    }

    // Update statistics numbers
    updateKPIs();

    // Render Charts
    initCharts();

    // Render Table
    renderPaginatedTable();
  }

  function updateKPIs() {

    // Static totals from backend
    document.getElementById("val-total-articles").textContent =
      dashboardStats.total_articles ?? "-";

    document.getElementById("val-dawn-articles").textContent =
      dashboardStats.dawn_articles ?? "-";

    document.getElementById("val-ummat-articles").textContent =
      dashboardStats.ummat_articles ?? "-";

    document.getElementById("val-total-matches").textContent =
      dashboardStats.total_matches ?? "-";

    // Dynamic values based on current filters
    const matchesCount = filteredMatches.length;

    const mediumCount = filteredMatches.filter(
      m => m.matchLevel === "Medium"
    ).length;

    const lowCount = filteredMatches.filter(
      m => m.matchLevel === "Low"
    ).length;

    document.getElementById("val-medium-matches").textContent = mediumCount;
    document.getElementById("val-low-matches").textContent = lowCount;

    const mediumPercent =
      matchesCount ? Math.round((mediumCount / matchesCount) * 100) : 0;

    const lowPercent =
      matchesCount ? Math.round((lowCount / matchesCount) * 100) : 0;

    document.getElementById("val-medium-percent").textContent =
      `${mediumPercent}% of current matches`;

    document.getElementById("val-low-percent").textContent =
      `${lowPercent}% of current matches`;
  }

  // --- Reset Filter Handler ---
  function resetFilters() {
    filterSearch.value = "";
    filterMatchLevel.value = "All";
    filterMinRelevance.value = 0;
    relevanceSliderVal.textContent = "0%";
    filterSort.value = "highest";
    activeHeaderSort = { field: null, order: 'desc' };
    resetHeaderIcons();
    currentPage = 1;
    applyFiltersAndRender();
  }

  function updateHeaderIcon(element, iconName) {
    const wrapper = element.querySelector(".sort-icon-wrapper");
    if (wrapper) {
      wrapper.innerHTML = `<i data-lucide="${iconName}" style="width: 12px; height: 12px;"></i>`;
      lucide.createIcons();
    }
  }

  // --- Header Column Sorting Handler ---
  function handleHeaderSort(field, element) {
    if (activeHeaderSort.field === field) {
      // Toggle order
      activeHeaderSort.order = activeHeaderSort.order === 'desc' ? 'asc' : 'desc';
    } else {
      activeHeaderSort.field = field;
      activeHeaderSort.order = 'desc';
    }

    // Reset indicator icons on other headers
    resetHeaderIcons();

    // Set sorting icon on current header element
    updateHeaderIcon(element, activeHeaderSort.order === 'asc' ? "chevron-up" : "chevron-down");

    currentPage = 1;
    applyFiltersAndRender();
  }

  function resetHeaderIcons() {
    const defaultIcon = "chevrons-up-down";
    updateHeaderIcon(thTextSim, defaultIcon);
    updateHeaderIcon(thImageSim, defaultIcon);
    updateHeaderIcon(thOverall, defaultIcon);
  }

  // --- Table Rendering with Pagination ---
  function renderPaginatedTable() {
    resultsCount.textContent = `${filteredMatches.length} matches found`;

    // Pagination math
    const totalItems = filteredMatches.length;
    const maxPages = Math.ceil(totalItems / rowsPerPage) || 1;

    if (currentPage > maxPages) currentPage = maxPages;

    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = Math.min(startIndex + rowsPerPage, totalItems);

    const paginatedItems = filteredMatches.slice(startIndex, endIndex);

    // Render Table Rows
    if (paginatedItems.length === 0) {
      matchesTableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
            <div style="display: flex; flex-direction: column; align-items: center; gap: 12px;">
              <i data-lucide="inbox" style="width: 40px; height: 40px; color: var(--text-muted);"></i>
              <span style="font-weight: 500; font-size: 1rem;">No article matches found</span>
              <span style="font-size: 0.85rem; color: var(--text-muted);">Try adjusting your search criteria, relevance slider or level filters.</span>
            </div>
          </td>
        </tr>
      `;
      lucide.createIcons();

      // Update pagination info
      paginationInfo.textContent = `Showing 0 to 0 of 0 matches`;
      btnPrevPage.disabled = true;
      btnNextPage.disabled = true;
      return;
    }

    let rowsHTML = "";
    paginatedItems.forEach(item => {
      const matchBadgeClass = (item.matchLevel || "").toLowerCase();
      const safeDawnHL = escapeHTML(item.dawnHeadline);
      const safeUmmatHL = escapeHTML(item.ummatHeadline);
      const safeDawnImg = escapeHTML(item.dawnImage || "");
      const safeUmmatImg = escapeHTML(item.ummatImage || "");

      rowsHTML += `
        <tr>
          <!-- Dawn Article -->
          <td>
            <div class="col-image-headline">
              <img src="${safeDawnImg}" alt="Dawn thumbnail" class="news-thumbnail" onerror="this.style.display='none'">
              <div class="headline-text">${safeDawnHL}</div>
            </div>
          </td>
          
          <!-- Ummat Article -->
          <td>
            <div class="col-image-headline">
              <img src="${safeUmmatImg}" alt="Daily Ummat thumbnail" class="news-thumbnail" onerror="this.style.display='none'">
              <div class="headline-text urdu-text">${safeUmmatHL}</div>
            </div>
          </td>
          
          <!-- Text Similarity -->
          <td>
            <div class="similarity-cell-wrapper">
              <span class="similarity-val-label">${item.textSimilarity}%</span>
              <div class="similarity-bar-bg">
                <div class="similarity-bar-fill text-fill" data-value="${item.textSimilarity}"></div>
              </div>
            </div>
          </td>
          
          <!-- Image Similarity -->
          <td>
            <div class="similarity-cell-wrapper">
              <span class="similarity-val-label">${item.imageSimilarity}%</span>
              <div class="similarity-bar-bg">
                <div class="similarity-bar-fill image-fill" data-value="${item.imageSimilarity}"></div>
              </div>
            </div>
          </td>
          
          <!-- Overall Score -->
          <td>
            <div class="overall-score-badge" style="
              border-color: ${item.matchLevel === 'High' ? 'var(--color-high-text)' :
          item.matchLevel === 'Medium' ? 'var(--color-medium-text)' :
            'var(--color-low-text)'
        };
              background-color: ${item.matchLevel === 'High' ? 'var(--color-high-bg)' :
          item.matchLevel === 'Medium' ? 'var(--color-medium-bg)' :
            'var(--color-low-bg)'
        };
              color: ${item.matchLevel === 'High' ? 'var(--color-high-text)' :
          item.matchLevel === 'Medium' ? 'var(--color-medium-text)' :
            'var(--color-low-text)'
        };
            ">
              ${item.overallScore}
            </div>
          </td>
          
          <!-- Match Badge -->
          <td>
            <span class="match-badge ${matchBadgeClass}">
              <span style="width: 6px; height: 6px; border-radius: 50%; background-color: currentColor;"></span>
              ${item.matchLevel} Match
            </span>
          </td>
        </tr>
      `;
    });

    matchesTableBody.innerHTML = rowsHTML;

    // Trigger smooth transitions on the similarity bars after mounting
    setTimeout(() => {
      const bars = document.querySelectorAll(".similarity-bar-fill");
      bars.forEach(bar => {
        const val = bar.getAttribute("data-value");
        bar.style.width = `${val}%`;
      });
    }, 100);

    // Update pagination controls
    paginationInfo.textContent = `Showing ${startIndex + 1} to ${endIndex} of ${totalItems} matches`;

    btnPrevPage.disabled = currentPage === 1;
    btnNextPage.disabled = currentPage === maxPages;

    lucide.createIcons();
  }

  // --- Dynamic Chart.js Creation ---
  function getThemeColors() {
    if (isDarkMode) {
      return {
        text: "#94A3B8",        // slate-400
        grid: "#1E293B",        // slate-800
        tooltipBg: "#0F172A",
        tooltipBorder: "#1E293B",
        cardBg: "#0F172A"
      };
    } else {
      return {
        text: "#334155",        // slate-700 (darker and more professional)
        grid: "#CBD5E1",        // slate-300 (darker lines)
        tooltipBg: "#FFFFFF",
        tooltipBorder: "#CBD5E1",
        cardBg: "#FFFFFF"
      };
    }
  }

  function initCharts() {
    const themeColors = getThemeColors();

    // 1. Destroy existing charts to prevent memory leak / overlapping images
    if (pieChartInstance) pieChartInstance.destroy();
    if (barChartInstance) barChartInstance.destroy();

    // Aggregate Data for Pie Chart (Match Levels in filtered results)
    const levelCounts = {
      High: filteredMatches.filter(m => m.matchLevel === "High").length,
      Medium: filteredMatches.filter(m => m.matchLevel === "Medium").length,
      Low: filteredMatches.filter(m => m.matchLevel === "Low").length
    };

    // Aggregate Data for Category Bar Chart
    const categories = [...new Set(allMatches.map(m => m.category))];
    const dawnCategoryCounts = Array(categories.length).fill(0);
    const ummatCategoryCounts = Array(categories.length).fill(0);

    filteredMatches.forEach(item => {
      const idx = categories.indexOf(item.category);
      if (idx !== -1) {
        dawnCategoryCounts[idx]++;
        ummatCategoryCounts[idx]++; // Since they are matching pairs, counts align per match
      }
    });

    // 2. Render Pie Chart
    const ctxPie = document.getElementById("pieChart").getContext("2d");

    // High-fidelity SaaS look colors (Stripe/Linear styled palette)
    const pieColors = {
      light: ["#10B981", "#F59E0B", "#EF4444"], // Emerald, Amber, Red
      dark: ["#34D399", "#FBBF24", "#F87171"]
    };
    const activePieColors = isDarkMode ? pieColors.dark : pieColors.light;

    // Handle empty data state visually on charts
    const hasPieData = Object.values(levelCounts).some(v => v > 0);
    const pieDataValues = hasPieData ? [levelCounts.High, levelCounts.Medium, levelCounts.Low] : [0, 0, 0];

    pieChartInstance = new Chart(ctxPie, {
      type: "doughnut",
      data: {
        labels: ["High Match", "Medium Match", "Low Match"],
        datasets: [{
          data: pieDataValues,
          backgroundColor: hasPieData ? activePieColors : ["#E2E8F0", "#E2E8F0", "#E2E8F0"],
          borderWidth: isDarkMode ? 2 : 1.5,
          borderColor: themeColors.cardBg,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "65%",
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              font: { family: "Inter", size: 12, weight: 500 },
              color: themeColors.text,
              padding: 18,
              usePointStyle: true,
              pointStyle: "circle"
            }
          },
          tooltip: {
            backgroundColor: themeColors.tooltipBg,
            titleColor: isDarkMode ? "#F8FAFC" : "#0F172A",
            bodyColor: themeColors.text,
            borderColor: themeColors.tooltipBorder,
            borderWidth: 1,
            titleFont: { family: "Inter", weight: 600 },
            bodyFont: { family: "Inter" },
            padding: 10,
            displayColors: true,
            callbacks: {
              label: function (context) {
                if (!hasPieData) return " No data available";
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const val = context.raw;
                const pct = Math.round((val / total) * 100);
                return ` ${context.label}: ${val} (${pct}%)`;
              }
            }
          }
        }
      }
    });

    // 3. Render Bar Chart (Grouped Dawn vs Daily Ummat Category Counts)
    const ctxBar = document.getElementById("barChart").getContext("2d");
    const hasBarData = filteredMatches.length > 0;

    // Filter categories to show only those with matches present (makes chart cleaner)
    const visibleCategories = [];
    const visibleDawnCounts = [];
    const visibleUmmatCounts = [];

    categories.forEach((cat, idx) => {
      if (dawnCategoryCounts[idx] > 0 || ummatCategoryCounts[idx] > 0) {
        visibleCategories.push(cat);
        visibleDawnCounts.push(dawnCategoryCounts[idx]);
        visibleUmmatCounts.push(ummatCategoryCounts[idx]);
      }
    });

    // Default placeholder display in chart if empty data
    const chartLabels = ["Dawn (English), Daily Ummat (Urdu)"];
    const datasetDawn = [
      dashboardStats.dawn_articles || 0
    ];

    const datasetUmmat = [
      dashboardStats.ummat_articles || 0
    ];

    barChartInstance = new Chart(ctxBar, {
      type: "bar",
      data: {
        labels: ["Articles"],
        datasets: [
          {
            label: "Dawn (English)",
            data: datasetDawn,
            backgroundColor: isDarkMode ? "#3B82F6" : "#1E3A8A", // Deep Navy Accent in light mode
            borderRadius: 4,
            barPercentage: 0.8,
            categoryPercentage: 0.6
          },
          {
            label: "Daily Ummat (Urdu)",
            data: datasetUmmat,
            backgroundColor: isDarkMode ? "#10B981" : "#10B981", // Emerald accent
            borderRadius: 4,
            barPercentage: 0.8,
            categoryPercentage: 0.6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: themeColors.text,
              font: { family: "Inter", size: 11 }
            }
          },
          y: {
            grid: {
              color: themeColors.grid,
              drawBorder: false
            },
            ticks: {
              color: themeColors.text,
              font: { family: "Inter", size: 11 },
              stepSize: 1,
              precision: 0
            }
          }
        },
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              font: { family: "Inter", size: 12, weight: 500 },
              color: themeColors.text,
              padding: 18,
              usePointStyle: true,
              pointStyle: "circle"
            }
          },
          tooltip: {
            backgroundColor: themeColors.tooltipBg,
            titleColor: isDarkMode ? "#F8FAFC" : "#0F172A",
            bodyColor: themeColors.text,
            borderColor: themeColors.tooltipBorder,
            borderWidth: 1,
            titleFont: { family: "Inter", weight: 600 },
            bodyFont: { family: "Inter" },
            padding: 10
          }
        }
      }
    });
  }

  // --- Flow Field Particle Background ---
  function initParticleBackground() {
    const canvas = document.getElementById("particle-bg-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = window.innerWidth;
    let height = window.innerHeight;
    let particles = [];
    let animationFrameId;
    let mouse = { x: -1000, y: -1000 };

    // Parameters
    const particleCount = 200;
    const speed = 0.6;
    const trailOpacity = 0.12;

    class Particle {
      constructor() {
        this.reset();
      }

      update() {
        // Flow Field Angle (Simplex-ish noise pattern)
        const angle = (Math.cos(this.x * 0.005) + Math.sin(this.y * 0.005)) * Math.PI;

        // Apply force from flow field
        this.vx += Math.cos(angle) * 0.15 * speed;
        this.vy += Math.sin(angle) * 0.15 * speed;

        // Mouse Repulsion
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const interactionRadius = 150;

        if (distance < interactionRadius) {
          const force = (interactionRadius - distance) / interactionRadius;
          // Push particles away from cursor
          this.vx -= dx * force * 0.04;
          this.vy -= dy * force * 0.04;
        }

        // Apply Velocity & Friction
        this.x += this.vx;
        this.y += this.vy;
        this.vx *= 0.94;
        this.vy *= 0.94;

        // Age lifespan
        this.age++;
        if (this.age > this.life) {
          this.reset();
        }

        // Wrap around screen boundaries
        if (this.x < 0) this.x = width;
        if (this.x > width) this.x = 0;
        if (this.y < 0) this.y = height;
        if (this.y > height) this.y = 0;
      }

      reset() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = 0;
        this.vy = 0;
        this.age = 0;
        this.life = Math.random() * 200 + 100;
      }

      draw() {
        // Adapt color to dark/light theme dynamically
        if (isDarkMode) {
          ctx.fillStyle = "#818cf8"; // Indigo-400 for dark mode
        } else {
          ctx.fillStyle = "#93c5fd"; // Blue-300 for light mode
        }

        // Fade in and out based on lifespan age
        const alpha = 1 - Math.abs((this.age / this.life) - 0.5) * 2;
        ctx.globalAlpha = alpha * (isDarkMode ? 0.35 : 0.25); // subtle ambient visual opacity
        ctx.fillRect(this.x, this.y, 1.8, 1.8);
      }
    }

    function initCanvas() {
      width = window.innerWidth;
      height = window.innerHeight;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      particles = [];
      for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
      }
    }

    function animate() {
      // Trail effect: clear with small transparency
      if (isDarkMode) {
        ctx.fillStyle = `rgba(9, 13, 22, ${trailOpacity})`; // dark background overlay
      } else {
        ctx.fillStyle = `rgba(248, 250, 252, ${trailOpacity})`; // light background overlay
      }
      ctx.globalAlpha = 1.0;
      ctx.fillRect(0, 0, width, height);

      particles.forEach(p => {
        p.update();
        p.draw();
      });

      animationFrameId = requestAnimationFrame(animate);
    }

    // Resize listener
    window.addEventListener("resize", () => {
      initCanvas();
    });

    // Track mouse viewport coordinates for repulsion
    window.addEventListener("mousemove", (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    });

    window.addEventListener("mouseleave", () => {
      mouse.x = -1000;
      mouse.y = -1000;
    });

    // Start
    initCanvas();
    animate();
  }

  // --- Relevance Calculator ---
  async function computeRelevance() {
    const heading = document.getElementById("calc-heading").value.trim();
    const subheading = document.getElementById("calc-subheading").value.trim();
    const imageUrl = document.getElementById("calc-image").value.trim();
    const resultsDiv = document.getElementById("calc-results");
    const loadingDiv = document.getElementById("calc-loading");
    const errorDiv = document.getElementById("calc-error");
    const errorText = document.getElementById("calc-error-text");

    resultsDiv.classList.add("hidden");
    errorDiv.classList.add("hidden");

    if (!heading || !subheading) {
      errorText.textContent = "Both heading and sub-heading are required.";
      errorDiv.classList.remove("hidden");
      return;
    }

    loadingDiv.classList.remove("hidden");

    try {
      const body = { heading, sub_heading: subheading };
      if (imageUrl) body.image_url = imageUrl;

      const res = await fetch(`${BACKEND_BASE_URL}/relevance/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });

      if (!res.ok) throw new Error(`Request failed: ${res.status}`);

      const data = await res.json();

      // Scores as percentages
      const textPct = Math.round(data.text_similarity * 100);
      const overallPct = Math.round(data.relevance_score * 100);

      document.getElementById("calc-text-sim").textContent = `${textPct}%`;
      document.getElementById("calc-overall-score").textContent = `${overallPct}%`;
      document.getElementById("calc-text-fill").style.width = `${textPct}%`;
      document.getElementById("calc-overall-fill").style.width = `${overallPct}%`;

      // Match level badge
      const badge = document.getElementById("calc-match-level");
      const level = data.match_level;
      badge.textContent = `${level} Match`;
      badge.className = `match-badge ${level.toLowerCase()}`;

      // Image preview
      const previewDiv = document.getElementById("calc-image-preview");
      if (imageUrl && data.image_used) {
        document.getElementById("calc-preview-img").src = imageUrl;
        previewDiv.classList.remove("hidden");
      } else if (imageUrl) {
        document.getElementById("calc-preview-img").src = imageUrl;
        previewDiv.classList.remove("hidden");
      } else {
        previewDiv.classList.add("hidden");
      }

      resultsDiv.classList.remove("hidden");
    } catch (err) {
      console.error("Relevance calculator error:", err);
      errorText.textContent = err.message || "Failed to compute relevance score.";
      errorDiv.classList.remove("hidden");
    } finally {
      loadingDiv.classList.add("hidden");
    }
  }

  // --- Interactive 3D Tilt Cards effect ---
  function initTiltCards() {
    const cards = document.querySelectorAll(".card");
    cards.forEach(card => {
      // Create glare element dynamically if it doesn't exist
      let glare = card.querySelector(".card-glare");
      if (!glare) {
        glare = document.createElement("div");
        glare.className = "card-glare";
        card.appendChild(glare);
      }

      // Create spotlight border element dynamically if it doesn't exist
      let spotlight = card.querySelector(".card-spotlight");
      if (!spotlight) {
        spotlight = document.createElement("div");
        spotlight.className = "card-spotlight";
        card.appendChild(spotlight);
      }

      // Create outer glow shadow element dynamically if it doesn't exist
      let glowShadow = card.querySelector(".card-glow-shadow");
      if (!glowShadow) {
        glowShadow = document.createElement("div");
        glowShadow.className = "card-glow-shadow";
        card.appendChild(glowShadow);
      }

      card.addEventListener("mousemove", (e) => {
        const rect = card.getBoundingClientRect();
        // Mouse coordinate percentiles relative to the card dimensions
        const px = (e.clientX - rect.left) / rect.width;
        const py = (e.clientY - rect.top) / rect.height;

        const maxTilt = 10; // degrees
        const rotateY = (px - 0.5) * maxTilt;
        const rotateX = (0.5 - py) * maxTilt;

        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
        card.style.transition = "transform 0.05s ease-out, box-shadow 0.2s ease";
        card.classList.add("hovering");

        card.style.setProperty("--glare-x", `${px * 100}%`);
        card.style.setProperty("--glare-y", `${py * 100}%`);

        // Calculate offset mouse coordinate relative to the glow shadow element (offset by inset 30px)
        const shadowX = (e.clientX - rect.left) + 30;
        const shadowY = (e.clientY - rect.top) + 30;
        card.style.setProperty("--glare-x-offset", `${shadowX}px`);
        card.style.setProperty("--glare-y-offset", `${shadowY}px`);
      });

      card.addEventListener("mouseleave", () => {
        // Smooth snapback reset
        card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
        card.style.transition = "transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease";
        card.classList.remove("hovering");
      });
    });
  }

  // --- Run Initialization ---
  init();
});
