import Link from 'next/link';
import Image from 'next/image';
import { siteConfig } from '@/content/site';

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link className="brand-mark" href="/" aria-label="SystemVerilog Academy home">
        <span className="brand-symbol">
          <Image
            src="/images/systemverilog-academy-logo.png"
            alt=""
            width={28}
            height={28}
            priority
          />
        </span>
        <span>
          {siteConfig.name}
          <small>{siteConfig.subtitle}</small>
        </span>
      </Link>
      <nav className="header-nav" aria-label="Primary navigation">
        <Link href="/courses">Courses</Link>
        <Link href="/#tracks">Tracks</Link>
      </nav>
    </header>
  );
}
