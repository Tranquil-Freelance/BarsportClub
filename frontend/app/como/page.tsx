import Image from 'next/image';
import Link from 'next/link';

export default function Page() {
  return (
    <div className="bg-[#050810] min-h-screen flex flex-col items-center pt-6">
      <Link href="/" className="text-gray-400 mb-4 hover:text-white">← Torna alla Home</Link>
      <div className="w-full max-w-[1400px]">
        <Image 
          src="/mockup/como-full-mockup.png" 
          alt="Mockup Como" 
          width={1400} 
          height={3000} 
          priority
          className="w-full h-auto"
        />
      </div>
    </div>
  );
}
