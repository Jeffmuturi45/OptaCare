// ── App Shell ────────────────────────────────────────────────────────────────
function appShell() {
  return {
    sidebarCollapsed: window.innerWidth < 992,
    init() {
      window.addEventListener('resize', () => {
        this.sidebarCollapsed = window.innerWidth < 992;
      });
    }
  }
}

// ── Live Clock ────────────────────────────────────────────────────────────────
function liveClock() {
  return {
    time: '', date: '', greeting: '',
    use24h: window.OPTACARE_CONFIG?.clock24h ?? false,
    userName: window.OPTACARE_CONFIG?.userName ?? '',
    start() { this.tick(); setInterval(() => this.tick(), 1000); },
    tick() {
      const now = new Date();
      const h = now.getHours();
      this.greeting = h >= 5  && h < 12 ? 'Good morning'
                    : h >= 12 && h < 17 ? 'Good afternoon'
                    : h >= 17 && h < 21 ? 'Good evening'
                    : 'Good night';
      this.time = now.toLocaleTimeString('en-KE', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: !this.use24h
      });
      this.date = now.toLocaleDateString('en-KE', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
      });
    }
  }
}

// ── Notifications ─────────────────────────────────────────────────────────────
function notifications() {
  return {
    open: false,
    items: [],
    unread: 0,
    init() {
      // placeholder — real fetch wired when API endpoint exists
    },
    markAllRead() {
      this.items.forEach(n => n.is_read = true);
      this.unread = 0;
      this.open = false;
    }
  }
}

// ── PIN Overlay ───────────────────────────────────────────────────────────────
function pinOverlay() {
  return {
    show: window.OPTACARE_CONFIG?.requirePin ?? false,
    pin: '',
    error: '',
    pressKey(k) {
      if (k === '⌫') { this.pin = this.pin.slice(0, -1); return; }
      if (typeof k !== 'number' || this.pin.length >= 4) return;
      this.pin += String(k);
      if (this.pin.length === 4) this.verify();
    },
    async verify() {
      try {
        const r = await fetch('/auth/pin/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({ pin: this.pin })
        });
        const d = await r.json();
        if (d.ok) { this.show = false; this.pin = ''; this.error = ''; }
        else { this.error = 'Incorrect PIN. Try again.'; this.pin = ''; }
      } catch (_) { this.pin = ''; }
    }
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function getCookie(name) {
  const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}