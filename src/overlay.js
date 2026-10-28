// Neshan Scraper - Minimalist Floating Action Toolbar
(function() {
    // 1. Expose helpers on window immediately
    window.__neshan_last_confirm_choice = null;

    window.neshan_show_confirm = function(placeInfo, index, total) {
        window.__neshan_last_confirm_choice = null;
        const barIdle = document.getElementById('neshan-bar-idle');
        const barProgress = document.getElementById('neshan-bar-progress');
        const barConfirm = document.getElementById('neshan-bar-confirm');
        const barIndex = document.getElementById('neshan-bar-index');
        const barTitle = document.getElementById('neshan-bar-title');

        if (barIdle) barIdle.style.display = 'none';
        if (barProgress) barProgress.style.display = 'none';
        if (barConfirm) barConfirm.style.display = 'flex';
        if (barIndex) barIndex.textContent = `مکان ${index + 1} از ${total}`;
        if (barTitle) barTitle.textContent = (placeInfo && placeInfo.name) ? placeInfo.name : 'بدون نام';
    };

    window.neshan_hide_confirm = function() {
        const barConfirm = document.getElementById('neshan-bar-confirm');
        if (barConfirm) barConfirm.style.display = 'none';
    };

    window.neshan_update_progress = function(current, total, statusText) {
        const barIdle = document.getElementById('neshan-bar-idle');
        const barConfirm = document.getElementById('neshan-bar-confirm');
        const barProgress = document.getElementById('neshan-bar-progress');
        const barStatus = document.getElementById('neshan-bar-status-text');

        if (barIdle) barIdle.style.display = 'none';
        if (barConfirm) barConfirm.style.display = 'none';
        if (barProgress) barProgress.style.display = 'flex';
        if (barStatus) barStatus.textContent = statusText || `استخراج ${current} از ${total}`;

        if (current >= total || (statusText && (statusText.includes('پایان') || statusText.includes('یافت نشد')))) {
            setTimeout(() => {
                if (barProgress) barProgress.style.display = 'none';
                if (barIdle) barIdle.style.display = 'flex';
            }, 3000);
        }
    };

    // 2. Build DOM
    function initToolbarDOM() {
        if (document.getElementById('neshan-toolbar-root')) return;
        if (!document.body) {
            document.addEventListener('DOMContentLoaded', initToolbarDOM);
            return;
        }

        // Inject styles
        if (!document.getElementById('neshan-toolbar-styles')) {
            const style = document.createElement('style');
            style.id = 'neshan-toolbar-styles';
            style.textContent = `
                #neshan-toolbar-root {
                    position: fixed;
                    bottom: 24px;
                    left: 50%;
                    transform: translateX(-50%);
                    z-index: 99999999;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Vazirmatn", Tahoma, sans-serif;
                    direction: rtl;
                    text-align: right;
                    user-select: none;
                    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                }
                .neshan-toolbar-card {
                    background: rgba(15, 23, 42, 0.94);
                    backdrop-filter: blur(16px);
                    border: 1.5px solid rgba(255, 255, 255, 0.16);
                    border-radius: 20px;
                    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(0, 0, 0, 0.2);
                    padding: 10px 18px;
                    box-sizing: border-box;
                    color: #ffffff;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .neshan-btn {
                    border: none;
                    border-radius: 12px;
                    font-size: 13px;
                    font-weight: 700;
                    cursor: pointer;
                    transition: all 0.18s ease;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                    padding: 9px 15px;
                    font-family: inherit;
                    white-space: nowrap;
                }
                .neshan-btn:hover {
                    transform: translateY(-1.5px);
                    filter: brightness(1.08);
                }
                .neshan-btn:active {
                    transform: translateY(0);
                }
                .neshan-btn-start {
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: white;
                    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
                }
                .neshan-btn-approve {
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: white;
                    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
                }
                .neshan-btn-skip {
                    background: rgba(245, 158, 11, 0.18);
                    color: #fbbf24;
                    border: 1.5px solid rgba(245, 158, 11, 0.5);
                }
                .neshan-btn-skip:hover {
                    background: rgba(245, 158, 11, 0.28);
                }
                .neshan-btn-all {
                    background: rgba(99, 102, 241, 0.18);
                    color: #a5b4fc;
                    border: 1.5px solid rgba(99, 102, 241, 0.5);
                }
                .neshan-btn-all:hover {
                    background: rgba(99, 102, 241, 0.28);
                }
                .neshan-btn-stop {
                    background: rgba(239, 68, 68, 0.18);
                    color: #fca5a5;
                    border: 1.5px solid rgba(239, 68, 68, 0.5);
                }
                .neshan-btn-stop:hover {
                    background: rgba(239, 68, 68, 0.28);
                }
                .neshan-badge-index {
                    background: #2563eb;
                    color: white;
                    padding: 4px 10px;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 800;
                }
                .neshan-place-title {
                    font-size: 14.5px;
                    font-weight: 800;
                    color: #f8fafc;
                    max-width: 280px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                @keyframes neshan-spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }

        // Create Root Toolbar
        const root = document.createElement('div');
        root.id = 'neshan-toolbar-root';
        root.innerHTML = `
            <div class="neshan-toolbar-card">
                <!-- 1. Idle Bar -->
                <div id="neshan-bar-idle" style="display: flex; align-items: center; gap: 14px;">
                    <span style="font-size: 14px; font-weight: 800; color: #38bdf8;">📍 اسکرپر نشان</span>
                    <span style="font-size: 12px; color: #cbd5e1;">نقشه را به محدوده مورد نظر ببرید:</span>
                    <button id="neshan-btn-start" class="neshan-btn neshan-btn-start">
                        <span>🚀 شروع بررسی و استخراج</span>
                    </button>
                </div>

                <!-- 2. Confirm & Review Bar -->
                <div id="neshan-bar-confirm" style="display: none; align-items: center; gap: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span id="neshan-bar-index" class="neshan-badge-index">مکان ۱ از ۱۰</span>
                        <span id="neshan-bar-title" class="neshan-place-title">نام مکان</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button id="neshan-btn-approve" class="neshan-btn neshan-btn-approve" title="کلید میانبر: Enter یا y">
                            <span>✅ استخراج (Enter)</span>
                        </button>
                        <button id="neshan-btn-skip" class="neshan-btn neshan-btn-skip" title="کلید میانبر: s">
                            <span>⏭️ رد کردن (s)</span>
                        </button>
                        <button id="neshan-btn-all" class="neshan-btn neshan-btn-all" title="کلید میانبر: a">
                            <span>⚡ همه بدون سوال (a)</span>
                        </button>
                        <button id="neshan-btn-stop" class="neshan-btn neshan-btn-stop" title="کلید میانبر: q">
                            <span>⏹️ پایان (q)</span>
                        </button>
                    </div>
                </div>

                <!-- 3. Progress Bar -->
                <div id="neshan-bar-progress" style="display: none; align-items: center; gap: 12px;">
                    <div style="width: 18px; height: 18px; border: 2.5px solid rgba(255,255,255,0.25); border-top-color: #38bdf8; border-radius: 50%; animation: neshan-spin 0.8s linear infinite;"></div>
                    <span id="neshan-bar-status-text" style="font-size: 13px; font-weight: 700; color: #e2e8f0;">در حال استخراج...</span>
                </div>
            </div>
        `;
        document.body.appendChild(root);

        // Elements
        const barIdle = document.getElementById('neshan-bar-idle');
        const barConfirm = document.getElementById('neshan-bar-confirm');
        const barProgress = document.getElementById('neshan-bar-progress');
        const btnStart = document.getElementById('neshan-btn-start');
        const btnApprove = document.getElementById('neshan-btn-approve');
        const btnSkip = document.getElementById('neshan-btn-skip');
        const btnAll = document.getElementById('neshan-btn-all');
        const btnStop = document.getElementById('neshan-btn-stop');
        const barStatus = document.getElementById('neshan-bar-status-text');

        // Click Start Button
        btnStart.addEventListener('click', async () => {
            barIdle.style.display = 'none';
            barProgress.style.display = 'flex';
            barStatus.textContent = 'در حال بررسی مکان‌های این محدوده...';

            try {
                if (typeof window.__dispatch_ui_action === 'function') {
                    await window.__dispatch_ui_action({
                        type: 'start',
                        options: {}
                    });
                }
            } catch (err) {
                console.error('Error dispatching start:', err);
                barIdle.style.display = 'flex';
                barProgress.style.display = 'none';
            }
        });

        function handleChoice(choice) {
            window.__neshan_last_confirm_choice = choice;
            barConfirm.style.display = 'none';
            barProgress.style.display = 'flex';
            barStatus.textContent = choice === 'skip' ? 'در حال رفتن به مکان بعدی...' : 'در حال استخراج اطلاعات و دانلود عکس‌ها...';
        }

        btnApprove.addEventListener('click', () => handleChoice('approve'));
        btnSkip.addEventListener('click', () => handleChoice('skip'));
        btnAll.addEventListener('click', () => handleChoice('all'));
        btnStop.addEventListener('click', () => handleChoice('stop'));

        // Keyboard Shortcuts directly in browser window
        window.addEventListener('keydown', (e) => {
            if (!barConfirm || barConfirm.style.display === 'none') return;
            if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;

            if (e.key === 'Enter' || e.key === 'y' || e.key === 'Y') {
                e.preventDefault();
                btnApprove.click();
            } else if (e.key === 's' || e.key === 'S') {
                e.preventDefault();
                btnSkip.click();
            } else if (e.key === 'a' || e.key === 'A') {
                e.preventDefault();
                btnAll.click();
            } else if (e.key === 'q' || e.key === 'Q' || e.key === 'Escape') {
                e.preventDefault();
                btnStop.click();
            }
        });
    }

    initToolbarDOM();
})();
