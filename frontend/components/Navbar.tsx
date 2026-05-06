"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import UpcomingMatchesTicker from '@/components/UpcomingMatchesTicker';

export default function Navbar() {
    const pathname = usePathname();

    const navLinks = [
        { name: 'CAMPIONATI', path: '/campionati' },
        { name: 'BETTING', path: '/betting' },
        { name: 'MERITOMETRO', path: '/meritometro' },
        { name: 'SCOUT ENGINE', path: '/scout-engine' },
        { name: 'FANTA DRAFT', path: '/fanta-draft' },
    ];

    return (
        <nav className="w-full bg-[#0a192f] text-white shadow-md border-b border-slate-800">
            <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-20">
                    
                    {/* Logo & Brand barsport.club */}
                    <div className="flex-shrink-0 flex items-center gap-4">
                        <div className="w-10 h-10 relative flex items-center justify-center bg-[#FF2A6D] rounded-sm transform rotate-45 shadow-[0_0_10px_rgba(255,42,109,0.5)]">
                            <div className="w-5 h-5 bg-[#0a192f] border border-white"></div>
                        </div>
                        <Link href="/" className="font-black text-3xl tracking-tighter italic text-white drop-shadow-sm">
                            barsport<span className="text-slate-400">.club</span>
                        </Link>
                    </div>

                    {/* Navigation Links */}
                    <div className="hidden md:flex items-center gap-10">
                        {/* Upcoming Matches dropdown — before CAMPIONATI */}
                        <UpcomingMatchesTicker />

                        {navLinks.map((link) => {
                            const isActive = pathname.startsWith(link.path);
                            return (
                                <Link
                                    key={link.name}
                                    href={link.path}
                                    className={`relative py-7 text-sm font-bold tracking-widest uppercase transition-all duration-300 transform hover:-translate-y-0.5
                                        ${isActive ? 'text-white' : 'text-slate-400 hover:text-white'}
                                    `}
                                >
                                    {link.name}
                                    {isActive && (
                                        <span className="absolute bottom-0 left-0 w-full h-1 bg-[#FF2A6D] rounded-t-md shadow-[0_0_10px_#FF2A6D]"></span>
                                    )}
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </div>
        </nav>
    );
}