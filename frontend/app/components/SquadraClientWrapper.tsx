"use client";

import Image from "next/image";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import "../i18n/config";

interface SquadraClientWrapperProps {
  squadra: string;
  name: string;
  hasMockup: boolean;
}

export default function SquadraClientWrapper({
  squadra,
  name,
  hasMockup,
}: SquadraClientWrapperProps) {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-[#050810] pt-10" suppressHydrationWarning>
      {hasMockup ? (
        <div className="flex flex-col items-center justify-start px-4">
          <div className="w-full max-w-[1400px]">
            <Image
              src={`/mockup/${squadra}-full-mockup.png`}
              alt={`${name} — Full Screen Mockup`}
              width={1400}
              height={800}
              className="w-full h-auto object-contain"
              priority
              unoptimized
            />
          </div>
          <Link
            href="/"
            className="mt-6 text-[8px] font-black uppercase tracking-[0.3em] text-white/30 hover:text-white/60 transition-colors duration-200"
          >
            ← {t("squadra.back_home")}
          </Link>
        </div>
      ) : (
        /* Placeholder for missing mockup (e.g. Fiorentina) */
        <div className="h-full w-full flex flex-col items-center justify-center gap-6 px-6">
          <div className="relative w-28 h-28 md:w-36 md:h-36">
            <Image
              src={`/logos/${name}.png`}
              alt={name}
              fill
              className="object-contain opacity-40"
              unoptimized
            />
          </div>
          <h1 className="font-heading text-3xl md:text-5xl font-black uppercase tracking-tight text-white/10 text-center">
            {name}
          </h1>
          <div className="border border-white/10 px-8 py-4">
            <p className="text-[10px] md:text-xs font-black uppercase tracking-[0.35em] text-white/30 text-center">
              {t("squadra.coming_soon")}
            </p>
          </div>
          <Link
            href="/"
            className="mt-4 text-[8px] font-black uppercase tracking-[0.3em] text-white/20 hover:text-white/50 transition-colors duration-200"
          >
            ← {t("squadra.back_home")}
          </Link>
        </div>
      )}
    </div>
  );
}
