"use client";

import { Globe, Instagram, Twitter, Youtube } from 'lucide-react';
import Link from 'next/link';
import { useTranslation } from "react-i18next";
import "../i18n/config";

export default function Footer() {
  const { t } = useTranslation();
  const currentYear = new Date().getFullYear();

  const socialLinks = [
    { icon: Globe, href: 'https://barsport.club', label: t('footer.social_website') },
    { icon: Instagram, href: 'https://instagram.com/barsport.club', label: t('footer.social_instagram') },
    { icon: Twitter, href: 'https://twitter.com/barsportclub', label: t('footer.social_twitter') },
    { icon: Youtube, href: 'https://youtube.com/@barsportclub', label: t('footer.social_youtube') },
  ];

  return (
    <footer className="bg-[#0A192F] text-white border-t-8 border-[#FF2A6D]" suppressHydrationWarning>
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          {/* Logo e brand */}
          <div className="flex-shrink-0 flex items-center gap-4">
            <div className="w-10 h-10 relative flex items-center justify-center bg-[#FF2A6D] rounded-sm transform rotate-45 shadow-[0_0_10px_rgba(255,42,109,0.5)]">
              <div className="w-5 h-5 bg-[#0A192F] border border-white"></div>
            </div>
            <div>
              <h2 className="font-black text-2xl tracking-tighter italic text-white drop-shadow-sm">
                barsport<span className="text-slate-400">.club</span>
              </h2>
              <p className="text-slate-400 text-sm mt-1">
                {t('footer.tagline')}
              </p>
            </div>
          </div>

          {/* Social icons */}
          <div className="flex items-center gap-6">
            {socialLinks.map(({ icon: Icon, href, label }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="group p-3 rounded-full bg-slate-800/50 hover:bg-slate-700 transition-colors duration-300"
                aria-label={label}
              >
                <Icon className="w-6 h-6 text-slate-300 group-hover:text-white transition-colors duration-300" />
              </a>
            ))}
          </div>

          {/* Copyright */}
          <div className="text-slate-400 text-sm text-center md:text-right">
            <p>{t('footer.copyright', { year: currentYear })}</p>
            <p className="mt-1">
              Dati forniti da fonti terze di analisi calcistica avanzata. Questo sito è un progetto amatoriale. Tutti i marchi appartengono ai rispettivi proprietari.
            </p>
            <Link
              href="/data-sources"
              className="mt-2 inline-block text-[10px] text-slate-700 hover:text-slate-500 transition-colors"
            >
              ℹ Fonti dati
            </Link>
          </div>
        </div>

        {/* Divider */}
        <div className="mt-12 pt-8 border-t border-slate-800/50 text-slate-500 text-xs text-center">
          <p>
            {t('footer.fan_project_disclaimer')}
          </p>
          <p className="mt-2">
            <Link href="/privacy" className="hover:text-slate-300 transition-colors">
              {t('footer.privacy_policy')}
            </Link>
            {' · '}
            <Link href="/terms" className="hover:text-slate-300 transition-colors">
              {t('footer.terms_of_service')}
            </Link>
            {' · '}
            <Link href="/contact" className="hover:text-slate-300 transition-colors">
              {t('footer.contact')}
            </Link>
          </p>
        </div>
      </div>
    </footer>
  );
}
