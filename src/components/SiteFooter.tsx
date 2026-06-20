import { siteConfig } from '@/content/site';

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div>
        <strong>{siteConfig.name}</strong>
        <p>SystemVerilog, digital design, and verification learning.</p>
      </div>
      <div className="footer-links">
        <a href={`mailto:${siteConfig.contactEmail}`}>{siteConfig.contactEmail}</a>
        <a href={siteConfig.youtubeUrl} target="_blank" rel="noreferrer">
          YouTube channel
        </a>
        <a href={siteConfig.linkedinUrl} target="_blank" rel="noreferrer">
          LinkedIn
        </a>
      </div>
    </footer>
  );
}
