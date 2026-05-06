import React from 'react';
import Link from 'next/link';

export interface NavbarProps {
  className?: string;
}

const Navbar: React.FC<NavbarProps> = ({ className = '' }) => {
  const navItems = [
    { label: 'Home', href: '/' },
    { label: 'Blog Palermo', href: '/blog-palermo' },
    { label: 'Stats Serie A', href: '/stats/serie-a' },
    { label: 'Premier League', href: '/stats/premier-league' },
    { label: 'Database', href: '/database' },
  ];

  return (
    <nav
      className={`navbar ${className} bg-zinc-950 border-b border-zinc-800/60 backdrop-blur-lg`}
      role="navigation"
    >
      <div className="container mx-auto px-6 py-4 flex flex-col md:flex-row justify-between items-center">
        {/* Logo */}
        <div className="flex items-center mb-4 md:mb-0">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-palermo-pink to-purple-600 flex items-center justify-center mr-3">
            <span className="text-lg font-heading font-bold text-white">XPS</span>
          </div>
          <Link
            href="/"
            className="text-2xl font-heading font-bold tracking-tight text-white"
          >
            xPalermo<span className="text-palermo-pink">Stat</span>
          </Link>
        </div>

        {/* Navigation Links */}
        <ul className="flex flex-wrap justify-center gap-6 md:gap-10">
          {navItems.map((item) => (
            <li key={item.label}>
              <Link
                href={item.href}
                className="text-sm uppercase font-heading font-bold tracking-wider text-zinc-300 hover:text-palermo-pink transition-all duration-300 transform hover:-translate-y-0.5"
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>

        {/* CTA Button */}
        <div className="mt-4 md:mt-0">
          <button className="px-6 py-3 bg-gradient-to-r from-palermo-pink to-purple-600 text-white font-heading font-bold uppercase tracking-wider rounded-xl hover:shadow-2xl hover:shadow-pink-900/50 hover:scale-105 transition-all duration-300">
            Report Partita
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;