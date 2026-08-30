/**
 * GRAIN Sandbox Experiment Server - Alpine.js Application Controller
 * Version: 2.0.0
 */

function catalogApp() {
    return {
        // Application Views & Navigation
        viewMode: 'grid', // 'grid' | 'explorer'
        searchQuery: '',
        filterType: 'all', // 'all' | 'video' | 'image' | 'document' | 'archive'
        isSearching: false,
        isLoading: false,
        isLoadingFolder: false,

        // Data Models
        stats: {
            total_experiments: 0,
            total_videos: 0,
            total_photos: 0,
            total_files: 0,
            total_size_formatted: '0 B',
            total_size_bytes: 0,
            last_sync: null
        },
        experiments: [],
        searchResults: [],
        
        // Experiment Detail Modal / Drawer
        selectedExperiment: null,
        showExpDetailModal: false,
        expTab: 'all', // 'all' | 'video' | 'image' | 'document' | 'archive'

        // File Explorer View Data
        currentFolderId: 'root',
        currentFolder: null,
        currentFolderItems: [],
        breadcrumbs: [],

        // Media Player & Lightbox
        activeModal: null, // 'video' | 'image' | null
        currentMedia: {},
        playbackRate: 1.0,

        // Sync Modal & State
        showSyncModal: false,
        isSyncing: false,
        syncScannedCount: 0,
        adminPinInput: '',
        syncError: '',
        syncSuccess: '',
        pollTimer: null,

        /**
         * Initialize component on mount
         */
        async init() {
            this.isLoading = true;
            await Promise.all([
                this.loadStats(),
                this.loadExperiments()
            ]);
            this.isLoading = false;

            // Check if a background sync is currently running
            this.checkInitialSyncStatus();
        },

        /**
         * Fetch catalog overview statistics
         */
        async loadStats() {
            try {
                const res = await fetch('/api/stats');
                if (res.ok) {
                    this.stats = await res.json();
                }
            } catch (err) {
                console.error('Failed to load stats:', err);
            }
        },

        /**
         * Fetch all Level-1 Experiment Folders
         */
        async loadExperiments() {
            try {
                const res = await fetch('/api/experiments');
                if (res.ok) {
                    this.experiments = await res.json();
                }
            } catch (err) {
                console.error('Failed to load experiments:', err);
            }
        },

        /**
         * Switch between Card Grid and File Explorer views
         */
        switchView(mode) {
            this.viewMode = mode;
            if (mode === 'explorer' && this.currentFolderItems.length === 0) {
                this.loadFolderItems('root');
            }
        },

        /**
         * Open Experiment Detail Modal & fetch full file list
         */
        async openExperiment(folderId) {
            try {
                this.isLoading = true;
                const res = await fetch(`/api/experiments/${folderId}`);
                if (!res.ok) {
                    throw new Error('Gagal mengambil data eksperimen.');
                }
                this.selectedExperiment = await res.json();
                this.expTab = 'all';
                this.showExpDetailModal = true;
            } catch (err) {
                alert(err.message);
            } finally {
                this.isLoading = false;
            }
        },

        closeExperimentModal() {
            this.showExpDetailModal = false;
            this.selectedExperiment = null;
        },

        /**
         * Open a folder in Explorer view from anywhere
         */
        openFolderInExplorer(folderId) {
            this.showExpDetailModal = false;
            this.viewMode = 'explorer';
            this.loadFolderItems(folderId);
        },

        /**
         * Load items and breadcrumbs for File Explorer
         */
        async loadFolderItems(folderId) {
            this.isLoadingFolder = true;
            this.currentFolderId = folderId;
            try {
                const res = await fetch(`/api/folders/${folderId}/items`);
                if (res.ok) {
                    const data = await res.json();
                    this.currentFolder = data.current_folder;
                    this.breadcrumbs = data.breadcrumbs || [];
                    this.currentFolderItems = data.items || [];
                }
            } catch (err) {
                console.error('Failed to load folder items:', err);
            } finally {
                this.isLoadingFolder = false;
            }
        },

        /**
         * Filter Experiments in Grid View
         */
        get filteredExperiments() {
            if (!this.experiments) return [];
            let list = [...this.experiments];

            if (this.filterType === 'video') {
                list = list.filter(e => e.video_count > 0);
            } else if (this.filterType === 'image') {
                list = list.filter(e => e.photo_count > 0);
            } else if (this.filterType === 'document') {
                list = list.filter(e => e.other_count > 0);
            }

            if (this.searchQuery.trim()) {
                const q = this.searchQuery.toLowerCase();
                list = list.filter(e => e.name.toLowerCase().includes(q) || (e.description && e.description.toLowerCase().includes(q)));
            }

            return list;
        },

        /**
         * Filter items inside Experiment Detail modal
         */
        get filteredExpFiles() {
            if (!this.selectedExperiment || !this.selectedExperiment.files) return [];
            if (this.expTab === 'all') return this.selectedExperiment.files;
            return this.selectedExperiment.files.filter(f => f.file_type === this.expTab);
        },

        /**
         * Quick Filter Tab Pill Selector
         */
        setFilter(type) {
            this.filterType = type;
            if (this.searchQuery.trim() || this.viewMode === 'search') {
                this.performSearch();
            }
        },

        /**
         * Instant Search Files API Call
         */
        async performSearch() {
            const query = this.searchQuery.trim();
            if (!query && this.filterType === 'all') {
                this.isSearching = false;
                this.searchResults = [];
                return;
            }

            this.isSearching = true;
            try {
                let url = `/api/search?q=${encodeURIComponent(query)}`;
                if (this.filterType !== 'all') {
                    url += `&file_type=${encodeURIComponent(this.filterType)}`;
                }
                const res = await fetch(url);
                if (res.ok) {
                    this.searchResults = await res.json();
                }
            } catch (err) {
                console.error('Search failed:', err);
            }
        },

        /**
         * Clear active search query
         */
        clearSearch() {
            this.searchQuery = '';
            this.isSearching = false;
            this.searchResults = [];
        },

        /**
         * Open Media Viewer (Video Player / Image Lightbox)
         */
        openMedia(file) {
            this.currentMedia = { ...file };
            this.playbackRate = 1.0;

            if (file.file_type === 'video' || file.name.match(/\.(mp4|mov|avi|webm|mkv)$/i)) {
                this.activeModal = 'video';
                this.$nextTick(() => {
                    const videoEl = document.getElementById('videoPlayerElement');
                    if (videoEl) {
                        videoEl.playbackRate = 1.0;
                        videoEl.currentTime = 0;
                        videoEl.play().catch(() => {});
                    }
                });
            } else if (file.file_type === 'image' || file.name.match(/\.(jpg|jpeg|png|webp|gif|bmp|tif|tiff)$/i)) {
                this.activeModal = 'image';
            } else {
                // For documents, download or open in new tab
                window.open(`/api/download/${file.file_id}?filename=${encodeURIComponent(file.name)}`, '_blank');
            }
        },

        /**
         * Change Video Playback Speed
         */
        setPlaybackSpeed(speed) {
            this.playbackRate = speed;
            const videoEl = document.getElementById('videoPlayerElement');
            if (videoEl) {
                videoEl.playbackRate = speed;
            }
        },

        /**
         * Close Media Modal
         */
        closeMediaModal() {
            const videoEl = document.getElementById('videoPlayerElement');
            if (videoEl) {
                videoEl.pause();
                videoEl.removeAttribute('src');
                videoEl.load();
            }
            this.activeModal = null;
            this.currentMedia = {};
        },

        /**
         * Open Sync Dialog
         */
        openSyncModal() {
            this.syncError = '';
            this.syncSuccess = '';
            this.adminPinInput = '';
            this.showSyncModal = true;
        },

        /**
         * Submit Sync Trigger Request
         */
        async submitSync() {
            if (!this.adminPinInput) {
                this.syncError = 'Silakan masukkan PIN Admin terlebih dahulu!';
                return;
            }

            this.syncError = '';
            this.syncSuccess = '';

            try {
                const res = await fetch('/api/sync/trigger', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ admin_pin: this.adminPinInput })
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Gagal memulai sinkronisasi.');
                }

                this.isSyncing = true;
                this.syncScannedCount = 0;
                this.pollSyncStatus();
            } catch (err) {
                this.syncError = err.message;
            }
        },

        /**
         * Check Initial Sync Status on Page Load
         */
        async checkInitialSyncStatus() {
            try {
                const res = await fetch('/api/sync/status');
                if (res.ok) {
                    const data = await res.json();
                    if (data.is_syncing) {
                        this.isSyncing = true;
                        this.syncScannedCount = data.current_scanned || 0;
                        this.pollSyncStatus();
                    }
                }
            } catch (err) {
                console.error('Error checking sync status:', err);
            }
        },

        /**
         * Poll Sync Status until Completed or Failed
         */
        pollSyncStatus() {
            if (this.pollTimer) clearInterval(this.pollTimer);

            this.pollTimer = setInterval(async () => {
                try {
                    const res = await fetch('/api/sync/status');
                    if (!res.ok) return;

                    const data = await res.json();
                    this.isSyncing = data.is_syncing;
                    this.syncScannedCount = data.current_scanned || 0;

                    if (!data.is_syncing) {
                        clearInterval(this.pollTimer);
                        this.pollTimer = null;

                        if (data.last_log && data.last_log.status === 'COMPLETED') {
                            this.syncSuccess = `Sinkronisasi selesai! ${data.last_log.total_files_scanned} file terpindai.`;
                        } else if (data.last_log && data.last_log.status === 'FAILED') {
                            this.syncError = data.last_log.message || 'Sinkronisasi gagal.';
                        }

                        // Refresh stats and experiment cards
                        await this.loadStats();
                        await this.loadExperiments();

                        if (this.viewMode === 'explorer') {
                            this.loadFolderItems(this.currentFolderId);
                        }
                    }
                } catch (err) {
                    console.error('Error polling sync status:', err);
                }
            }, 1500);
        },

        /**
         * Helper to format human-readable date strings
         */
        formatDate(isoString) {
            if (!isoString) return '-';
            try {
                const d = new Date(isoString);
                return d.toLocaleDateString('id-ID', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (e) {
                return isoString;
            }
        }
    };
}
