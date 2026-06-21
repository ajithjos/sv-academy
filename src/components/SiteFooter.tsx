import { Mail } from 'lucide-react';
import { siteConfig } from '@/content/site';

function YouTubeIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M21.6 7.2a3 3 0 0 0-2.1-2.1C17.6 4.6 12 4.6 12 4.6s-5.6 0-7.5.5a3 3 0 0 0-2.1 2.1A31.2 31.2 0 0 0 1.9 12c0 1.6.2 3.2.5 4.8a3 3 0 0 0 2.1 2.1c1.9.5 7.5.5 7.5.5s5.6 0 7.5-.5a3 3 0 0 0 2.1-2.1c.3-1.6.5-3.2.5-4.8s-.2-3.2-.5-4.8ZM10 15.5v-7l6 3.5-6 3.5Z"
        fill="currentColor"
      />
    </svg>
  );
}

function LinkedInIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M5.1 8.8h3.2v10.3H5.1V8.8Zm1.6-5.1a1.85 1.85 0 1 1 0 3.7 1.85 1.85 0 0 1 0-3.7Zm3.6 5.1h3.1v1.4h.1c.4-.8 1.5-1.7 3.1-1.7 3.3 0 3.9 2.2 3.9 5v5.6h-3.2v-5c0-1.2 0-2.7-1.7-2.7s-1.9 1.3-1.9 2.6v5.1h-3.2V8.8Z"
        fill="currentColor"
      />
    </svg>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div>
        <strong>{siteConfig.name}</strong>
        <p>SystemVerilog, digital design, and verification learning.</p>
      </div>
      <div className="footer-links">
        <a className="footer-email" href={`mailto:${siteConfig.contactEmail}`}>
          <Mail aria-hidden="true" />
          <span>{siteConfig.contactEmail}</span>
        </a>
        <a
          className="footer-icon-link"
          href={siteConfig.youtubeUrl}
          target="_blank"
          rel="noreferrer"
          aria-label="SystemVerilog Academy on YouTube"
        >
          <YouTubeIcon />
        </a>
        <a
          className="footer-icon-link"
          href={siteConfig.linkedinUrl}
          target="_blank"
          rel="noreferrer"
          aria-label="SystemVerilog Academy on LinkedIn"
        >
          <LinkedInIcon />
        </a>
      </div>
    </footer>
  );
}
