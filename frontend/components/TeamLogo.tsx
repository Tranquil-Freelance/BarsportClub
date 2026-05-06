"use client";

import React, { useState } from 'react';
import Image from 'next/image';

interface TeamLogoProps {
    teamName?: string; // Il '?' lo rende opzionale, salva il sito dai crash
    size?: number;
    className?: string;
}

export default function TeamLogo({ teamName, size = 40, className = "" }: TeamLogoProps) {
    const [hasError, setHasError] = useState(false);
    
    // PROTEZIONE ANTI-CRASH: Se teamName è vuoto o undefined, usiamo un fallback sicuro
    const safeName = teamName || "?";
    
    // Il percorso della cartella public/logos
    const imagePath = `/logos/${safeName}.png`;

    // IL FALLBACK: Se il logo manca fisicamente nella cartella o il nome è vuoto
    if (hasError || !teamName) {
        return (
            <div
                className={`flex items-center justify-center rounded-full bg-[#0a192f] border-2 border-[#FF2A6D] text-white font-black shadow-md ${className}`}
                // Math.max assicura che il font non scenda mai sotto i 14px, niente robe minuscole!
                style={{ width: size, height: size, fontSize: Math.max(14, size * 0.5) }} 
                title={teamName || "Squadra Sconosciuta"}
            >
                {safeName.charAt(0).toUpperCase()}
            </div>
        );
    }

    // IL LOGO REALE (Se l'immagine PNG esiste in public/logos)
    return (
        <div 
            style={{ width: size, height: size }} 
            className={`relative flex-shrink-0 flex items-center justify-center rounded-full overflow-hidden bg-white border border-slate-200 shadow-sm ${className}`}
        >
            <Image
                src={imagePath}
                alt={`${safeName} logo`}
                fill
                sizes={`${size}px`}
                className="object-contain p-1" // Il p-1 dà un po' di respiro al logo dentro il cerchio
                onError={() => setHasError(true)}
            />
        </div>
    );
}