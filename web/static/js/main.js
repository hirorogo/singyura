// 七並べAI - メインJavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('七並べAI Webサイトが読み込まれました');
    
    // スムーズスクロール
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // コードブロックのコピー機能
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        const button = document.createElement('button');
        button.textContent = 'コピー';
        button.className = 'copy-button';
        button.addEventListener('click', () => {
            navigator.clipboard.writeText(block.textContent);
            button.textContent = 'コピー完了！';
            setTimeout(() => {
                button.textContent = 'コピー';
            }, 2000);
        });
        block.parentElement.style.position = 'relative';
        block.parentElement.appendChild(button);
    });
    
    // ExoClick広告の読み込み確認
    const adElements = document.querySelectorAll('.ad-banner-top, .ad-sidebar');
    if (adElements.length > 0) {
        console.log(`${adElements.length}個の広告エリアを検出しました`);
    }
});

// ナビゲーションメニューのハイライト
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-menu a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.color = 'var(--primary-color)';
            link.style.borderBottom = '2px solid var(--primary-color)';
        }
    });
}

// ページ読み込み時に実行
window.addEventListener('load', highlightCurrentPage);

// スクロール時のアニメーション
function revealOnScroll() {
    const elements = document.querySelectorAll('.feature-card, .pricing-card, .support-card');
    
    elements.forEach(element => {
        const elementTop = element.getBoundingClientRect().top;
        const elementVisible = 150;
        
        if (elementTop < window.innerHeight - elementVisible) {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }
    });
}

window.addEventListener('scroll', revealOnScroll);

// 初期状態設定
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.feature-card, .pricing-card, .support-card');
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
    });
    revealOnScroll();
});
