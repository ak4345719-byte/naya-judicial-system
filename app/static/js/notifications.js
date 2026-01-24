
document.addEventListener('DOMContentLoaded', () => {
    const notifBtn = document.getElementById('notifBtn');
    const notifBadge = document.getElementById('notifBadge');
    const notifDropdown = document.getElementById('notifDropdown');
    const notifList = document.getElementById('notifList');

    
    notifBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        notifDropdown.classList.toggle('hidden');
    });

    
    document.addEventListener('click', (e) => {
        if (!notifDropdown.contains(e.target) && !notifBtn.contains(e.target)) {
            notifDropdown.classList.add('hidden');
        }
    });

    async function fetchNotifications() {
        try {
            const res = await fetch('/api/notifications');
            const data = await res.json();

            
            if (data.unread_count > 0) {
                notifBadge.textContent = data.unread_count > 9 ? '9+' : data.unread_count;
                notifBadge.classList.remove('hidden');
            } else {
                notifBadge.classList.add('hidden');
            }

            
            if (data.notifications.length === 0) {
                notifList.innerHTML = '<div class="p-4 text-center text-sm text-gray-500">No new notifications</div>';
            } else {
                notifList.innerHTML = data.notifications.map(n => {
                    let badgeColor = "bg-gray-100 text-gray-600";
                    let icon = "info-circle";

                    if (n.type === 'Success') { badgeColor = "bg-green-100 text-green-600"; icon = "check-circle"; }
                    if (n.type === 'Warning') { badgeColor = "bg-yellow-100 text-yellow-600"; icon = "exclamation-triangle"; }
                    if (n.type === 'Critical') { badgeColor = "bg-red-100 text-red-600"; icon = "bell"; }

                    return `
                    <div class="px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors ${!n.read ? 'bg-indigo-50/30' : ''}">
                        <div class="flex items-start gap-3">
                            <div class="mt-0.5 w-2 h-2 rounded-full ${!n.read ? 'bg-indigo-500' : 'bg-transparent'}"></div>
                            <div class="flex-1">
                                <p class="text-sm text-gray-700 leading-snug mb-1">${n.message}</p>
                                <div class="flex justify-between items-center">
                                    <span class="text-[10px] font-bold px-1.5 py-0.5 rounded ${badgeColor}">${n.type}</span>
                                    <span class="text-[10px] text-gray-400">${getTimeAgo(new Date(n.timestamp))}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    `;
                }).join('');
            }
        } catch (e) {
            console.error("Notif Poll Error", e);
        }
    }

    function getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        if (seconds < 60) return "Just now";
        if (seconds < 3600) return Math.floor(seconds / 60) + "m ago";
        if (seconds < 86400) return Math.floor(seconds / 3600) + "h ago";
        return Math.floor(seconds / 86400) + "d ago";
    }

    
    fetchNotifications();
    setInterval(fetchNotifications, 10000);
});
