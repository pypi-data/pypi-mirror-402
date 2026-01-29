DEFAULT_CSS = """@page {
    size: A4;
    margin: 2.5cm 2cm;

    @bottom-center {
        content: element(footer);
    }
}

@font-face {
    font-family: 'Inter';
    src: url('fonts/Inter-Regular.ttf');
    font-weight: 400;
}

@font-face {
    font-family: 'Inter';
    src: url('fonts/Inter-Medium.ttf');
    font-weight: 500;
}

@font-face {
    font-family: 'Inter';
    src: url('fonts/Inter-SemiBold.ttf');
    font-weight: 600;
}

@font-face {
    font-family: 'Inter';
    src: url('fonts/Inter-Bold.ttf');
    font-weight: 700;
}

:root {
    --primary: #1e293b;
    --secondary: #64748b;
    --accent: #7dd3fc;
    --accent-dark: #3b82f6;
    --surface: #f8fafc;
    --border: #e2e8f0;
    --muted: #94a3b8;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    line-height: 1.7;
    color: var(--primary);
}

.header {
    margin: -2.5cm -2cm 0 -2cm;
    padding: 2cm;
    background: linear-gradient(135deg, #0a0f1a, #0f172a, #1e293b);
    color: #ffffff;
    position: relative;
    overflow: hidden;
}

.header-content {
    position: relative;
    z-index: 1;
    display: flex;
    gap: 32px;
}

.header-logo {
    width: 110px;
    height: 110px;
    background: #fff;
    border-radius: 20px;
    padding: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, .3);
}

.header-logo img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

h1 {
    font-size: 32px;
    margin: 0;
    font-weight: 700;
}

.content h1 {
    margin: 48px 0 20px;
    position: relative;
    padding-bottom: 12px;
}

.content h1::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #7dd3fc, #3b82f6);
    border-radius: 2px;
}

.badge {
    display: inline-block;
    margin-top: 12px;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: #7dd3fc;
    background: rgba(59, 130, 246, .2);
    border-radius: 6px;
    border: 1px solid rgba(125, 211, 252, .3);
}

.header-date {
    margin-top: 20px;
    font-size: 13px;
    color: #94a3b8;
}

.content {
    margin-top: 30px;
}

.toc {
    margin: 28px 0 36px;
    padding: 24px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(59, 130, 246, .12), 0 0 0 1px rgba(125, 211, 252, .18);
    page-break-inside: avoid;
    break-inside: avoid;
}

.toc-heading {
    margin: 0 0 12px;
}

.toc-list {
    margin: 0;
    padding-left: 0;
    list-style: none;
}

.toc-list li {
    margin: 10px 0;
    padding-left: 0 !important;
}

.toc-list a {
    display: block;
    color: var(--secondary);
    text-decoration: none;
    font-weight: 600;
}

.toc-list a::after {
    content: leader('.') target-counter(attr(href), page);
    color: var(--muted);
    font-weight: 500;
}

.architecture-summary {
    page-break-inside: avoid;
    break-inside: avoid;
}

.architecture-diagram {
    margin: 24px 0;
    page-break-inside: avoid;
    break-inside: avoid;
    text-align: center;
}

.architecture-diagram img {
    width: 100%;
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}

h2 {
    font-size: 24px;
    margin: 48px 0 20px;
    font-weight: 700;
    position: relative;
    padding-bottom: 12px;
}

h2::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 60px;
    height: 4px;
    background: linear-gradient(90deg, #7dd3fc, #3b82f6);
    border-radius: 2px;
}

h3 {
    font-size: 18px;
    margin: 32px 0 16px;
    font-weight: 700;
    color: var(--primary);
    page-break-after: avoid;
    break-after: avoid;
}

h4 {
    font-size: 16px;
    margin: 24px 0 12px;
    font-weight: 600;
    color: var(--primary);
}

p {
    color: var(--secondary);
}

table {
    width: 100%;
    margin-top: 24px;
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    page-break-inside: avoid;
    break-inside: avoid;
}

thead {
    display: table-header-group;
}

tbody {
    display: table-row-group;
}

tr {
    page-break-inside: avoid;
    break-inside: avoid;
}

th,
td {
    padding: 14px 16px;
    font-size: 13px;
}

thead {
    background: linear-gradient(135deg, #0f172a, #1e293b);
}

thead th {
    color: white;
    font-size: 11px;
    text-transform: uppercase;
}

tbody tr:nth-child(even) {
    background: var(--surface);
}

.timeline {
    margin-top: 28px;
    padding-left: 30px;
    border-left: 3px solid #e0f2fe;
    page-break-inside: avoid;
    break-inside: avoid;
}

.timeline-item {
    margin-bottom: 26px;
    position: relative;
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: -38px;
    top: 4px;
    width: 14px;
    height: 14px;
    background: #3b82f6;
    border-radius: 50%;
    border: 3px solid white;
}

.timeline-item strong {
    display: block;
    margin-bottom: 4px;
    color: var(--primary);
}

.timeline-item p {
    margin: 0;
    color: var(--secondary);
}

ul {
    margin-top: 16px;
    padding-left: 0;
    list-style: none;
}

ul li {
    padding-left: 28px;
    margin-bottom: 10px;
    position: relative;
    color: var(--secondary);
}

ul li::before {
    content: '✔';
    position: absolute;
    left: 0;
    color: var(--accent-dark);
    font-weight: 700;
}

ul li.no-style::before,
.package-features li::before,
.toc-list li::before {
    content: none;
    display: none;
}

ul li.no-style,
.package-features li,
.toc-list li {
    padding-left: 0;
}

ol {
    margin-top: 16px;
    padding-left: 0;
    list-style: none;
    counter-reset: ol-counter;
}

ol li {
    padding-left: 40px;
    margin-bottom: 10px;
    position: relative;
    color: var(--secondary);
    counter-increment: ol-counter;
}

ol li::before {
    content: counter(ol-counter);
    position: absolute;
    left: 0;
    top: 0;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #7dd3fc, #3b82f6);
    color: white;
    font-weight: 700;
    font-size: 14px;
    border-radius: 50%;
    line-height: 1;
}

ol.no-style {
    margin-top: 16px;
    padding-left: 20px;
    list-style: decimal;
    counter-reset: none;
}

ol.no-style li {
    padding-left: 0;
    margin-bottom: 10px;
    position: static;
    color: var(--secondary);
    counter-increment: none;
}

ol.no-style li::before {
    content: none;
    display: none;
}

.info-cards {
    display: flex;
    justify-content: start;
    gap: 20px;
    margin-top: 24px;
    flex-wrap: wrap;
    page-break-inside: avoid;
    break-inside: avoid;
}

.info-card {
    flex: 0 1 calc(33.333% - 14px);
    min-width: 180px;
    max-width: 100%;
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 16px rgba(59, 130, 246, .15), 0 0 0 1px rgba(125, 211, 252, .2);
    position: relative;
    overflow: hidden;
    page-break-inside: avoid;
    break-inside: avoid;
}

@media (max-width: 600px) {
    .info-card {
        flex: 0 1 100%;
    }
}

.info-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #7dd3fc, #3b82f6);
}

.info-card h3 {
    margin: 0 0 8px;
    font-size: 16px;
    font-weight: 700;
    color: var(--primary);
}

.info-card p {
    margin: 0;
    font-size: 14px;
    color: var(--secondary);
}

.info-card .value {
    font-size: 24px;
    font-weight: 700;
    color: var(--accent-dark);
    margin: 8px 0 4px;
}

.summary-cards {
    display: flex;
    gap: 24px;
    margin-top: 24px;
    flex-wrap: wrap;
    page-break-inside: avoid;
    break-inside: avoid;
}

.summary-card {
    flex: 1;
    min-width: 220px;
    background: linear-gradient(135deg, #f8fafc, #ffffff);
    border: 2px solid var(--accent);
    border-radius: 16px;
    padding: 32px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, .08);
    position: relative;
    overflow: hidden;
    page-break-inside: avoid;
    break-inside: avoid;
}

.summary-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #7dd3fc, #3b82f6);
}

.summary-card h3 {
    margin: 0 0 16px;
    font-size: 13px;
    font-weight: 600;
    color: var(--secondary);
    text-transform: uppercase;
    letter-spacing: .5px;
}

.summary-card .value {
    font-size: 36px;
    font-weight: 700;
    color: var(--primary);
    margin: 0;
    line-height: 1.2;
}

.summary-card .label {
    font-size: 12px;
    color: var(--muted);
    margin-top: 8px;
}

.support-packages {
    display: flex;
    gap: 12px;
    margin-top: 24px;
    flex-wrap: nowrap;
    page-break-inside: avoid;
    break-inside: avoid;
}

.package-card {
    flex: 1 1 0;
    min-width: 0;
    max-width: 100%;
    background: white;
    border: 2px solid var(--border);
    border-radius: 16px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    page-break-inside: avoid;
    break-inside: avoid;
}

.package-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #7dd3fc, #3b82f6);
}

.package-card.featured {
    border-color: var(--accent-dark);
    box-shadow: 0 8px 24px rgba(59, 130, 246, .2);
}

.package-card.featured::before {
    height: 6px;
}

.package-header {
    text-align: center;
    margin-bottom: 16px;
}

.package-name {
    font-size: 18px;
    font-weight: 700;
    color: var(--primary);
    margin: 0 0 6px;
}

.package-price {
    font-size: 28px;
    font-weight: 700;
    color: var(--accent-dark);
    margin: 0;
}

.package-price-label {
    font-size: 11px;
    color: var(--muted);
    margin-top: 4px;
}

.package-features {
    margin: 16px 0;
    padding: 0;
    list-style: none;
}

.package-features li {
    padding: 8px 0 !important;
    border-bottom: 1px solid var(--surface);
    color: var(--secondary);
    font-size: 12px;
    line-height: 1.5;
}

.package-features li:last-child {
    border-bottom: none;
}

.package-features li strong {
    color: var(--primary);
    font-weight: 600;
}

.package-badge {
    display: inline-block;
    margin-bottom: 12px;
    padding: 4px 12px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    color: #fff;
    background: var(--accent-dark);
    border-radius: 12px;
}

.warranty-notice {
    background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    border-left: 4px solid var(--accent-dark);
    padding: 20px;
    margin-top: 24px;
    border-radius: 8px;
    page-break-inside: avoid;
    break-inside: avoid;
}

.warranty-notice p {
    margin: 0;
    color: var(--primary);
    font-size: 13px;
}

.warranty-notice strong {
    color: var(--accent-dark);
}

footer {
    position: running(footer);
    border-top: 2px solid var(--border);
    padding-top: 12px;
    font-size: 11px;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
}
"""
