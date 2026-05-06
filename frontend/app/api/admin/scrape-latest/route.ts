import { spawn } from 'child_process';
import { NextResponse } from 'next/server';
import path from 'path';

export async function POST() {
    try {
        // process.cwd() = frontend/ → risali di un livello per puntare alla root del progetto
        const projectRoot = path.resolve(process.cwd(), '..');
        const scriptPath = path.join(projectRoot, 'backend', 'scraper_ultime_giornate.py');

        const processPy = spawn('python3', [scriptPath], {
            detached: true,
            stdio: 'ignore',
        });
        processPy.unref(); // Sgancia il processo – non blocca l'API

        return NextResponse.json(
            { status: "success", message: "Scraping Ultime Giornate avviato in background" },
            { status: 200 }
        );
    } catch (error) {
        console.error('Errore avvio scraper ultime giornate:', error);
        return NextResponse.json(
            { status: "error", message: "Impossibile avviare il motore" },
            { status: 500 }
        );
    }
}
