"use client";

import { useState } from "react";
import { FileText, Tag, Film, Upload, Save, X, CheckCircle } from "lucide-react";

export default function ExerciseForm() {
  // Form state
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [animationUrl, setAnimationUrl] = useState("");
  const [explanation, setExplanation] = useState("");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Category options
  const categories = [
    "Tactical Analysis",
    "Player Performance",
    "Match Breakdown",
    "Statistical Insight",
    "Training Exercise",
    "Set Piece",
  ];

  // Handle drag‑over events
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type === "text/csv") {
      setCsvFile(file);
    } else {
      alert("Please drop a CSV file only.");
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === "text/csv") {
      setCsvFile(file);
    } else {
      alert("Please select a CSV file.");
    }
  };

  const handleRemoveFile = () => {
    setCsvFile(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !category || !explanation.trim()) {
      alert("Please fill in all required fields (Title, Category, Explanation).");
      return;
    }

    setIsSubmitting(true);
    // Simulate API call
    setTimeout(() => {
      setIsSubmitting(false);
      setShowSuccess(true);
      // Reset form after success
      setTitle("");
      setCategory("");
      setAnimationUrl("");
      setExplanation("");
      setCsvFile(null);
      // Hide success after 4 seconds
      setTimeout(() => setShowSuccess(false), 4000);
    }, 1500);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
          <FileText className="h-6 w-6 text-emerald-400" />
          Exercise Insertion Form
        </h2>
        <p className="mt-2 text-slate-400">
          Create new tactical exercises, insights, and analysis entries for the database.
        </p>
      </div>

      {/* Success Toast */}
      {showSuccess && (
        <div className="rounded-xl border border-emerald-800/50 bg-gradient-to-r from-emerald-900/40 to-emerald-950/40 p-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-900/80">
              <CheckCircle className="h-6 w-6 text-emerald-300" />
            </div>
            <div>
              <h4 className="font-bold text-emerald-300">Exercise Saved Successfully!</h4>
              <p className="mt-1 text-sm text-emerald-200/80">
                The exercise has been added to the database and is now visible in the insights library.
              </p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Two‑column layout for basic fields */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* Left column: Title & Category */}
          <div className="space-y-6">
            {/* Exercise Title */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Exercise Title <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., 'Breaking Low Block with Overloads'"
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3.5 text-white placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
                required
              />
              <p className="mt-2 text-xs text-slate-500">
                A concise, descriptive title that will appear in the exercise library.
              </p>
            </div>

            {/* Category Tag */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Category Tag <span className="text-rose-500">*</span>
              </label>
              <div className="flex flex-wrap gap-2 mb-3">
                {categories.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setCategory(cat)}
                    className={`px-4 py-2 rounded-full border text-sm font-medium transition-all ${category === cat
                        ? "border-emerald-600 bg-emerald-900/40 text-emerald-300"
                        : "border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600 hover:text-slate-300"
                      }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3.5 text-white focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
              >
                <option value="">Select a category</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Animation URL/ID */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Animation URL or ID
              </label>
              <div className="flex items-center gap-3">
                <Film className="h-5 w-5 text-slate-500" />
                <input
                  type="text"
                  value={animationUrl}
                  onChange={(e) => setAnimationUrl(e.target.value)}
                  placeholder="e.g., https://analytics.viz/anim/12345 or 12345"
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-4 py-3.5 text-white placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
                />
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Link to a tactical animation or internal ID for embedded visualisations.
              </p>
            </div>
          </div>

          {/* Right column: Drag‑and‑drop CSV area */}
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">
              Team/Player Data Import (CSV)
            </label>
            <div
              className={`rounded-2xl border-2 border-dashed ${isDragOver ? "border-emerald-500 bg-emerald-900/20" : "border-slate-700 bg-slate-900/30"
                } p-10 text-center transition-colors`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {csvFile ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-center gap-4 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
                    <FileText className="h-10 w-10 text-emerald-400" />
                    <div className="text-left">
                      <p className="font-medium text-white">{csvFile.name}</p>
                      <p className="text-sm text-slate-400">
                        {(csvFile.size / 1024).toFixed(1)} KB • Ready for ingestion
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleRemoveFile}
                      className="ml-auto rounded-full p-2 text-slate-500 hover:bg-slate-800 hover:text-white"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                  <p className="text-sm text-slate-400">
                    This CSV will be parsed for player/team statistics and linked to the exercise.
                  </p>
                </div>
              ) : (
                <>
                  <Upload className="mx-auto h-12 w-12 text-slate-500" />
                  <p className="mt-4 text-lg font-medium text-white">
                    Drop your CSV file here
                  </p>
                  <p className="mt-2 text-sm text-slate-400">
                    or{" "}
                    <label className="cursor-pointer text-emerald-400 hover:text-emerald-300">
                      browse
                      <input
                        type="file"
                        accept=".csv"
                        className="hidden"
                        onChange={handleFileSelect}
                      />
                    </label>{" "}
                    to upload
                  </p>
                  <p className="mt-4 text-xs text-slate-500">
                    Supports team line‑ups, player stats, match events. Max 10 MB.
                  </p>
                </>
              )}
            </div>
            <div className="mt-6 rounded-lg border border-slate-800 bg-slate-900/50 p-5">
              <h4 className="font-medium text-white flex items-center gap-2">
                <Tag className="h-4 w-4 text-slate-400" />
                CSV Import Notes
              </h4>
              <ul className="mt-3 space-y-2 text-sm text-slate-400">
                <li className="flex items-start gap-2">
                  <div className="h-1.5 w-1.5 mt-1.5 rounded-full bg-slate-600" />
                  Ensure columns: <code className="rounded bg-slate-800 px-1.5 py-0.5">player_id</code>,{" "}
                  <code className="rounded bg-slate-800 px-1.5 py-0.5">metric</code>,{" "}
                  <code className="rounded bg-slate-800 px-1.5 py-0.5">value</code>.
                </li>
                <li className="flex items-start gap-2">
                  <div className="h-1.5 w-1.5 mt-1.5 rounded-full bg-slate-600" />
                  First row must be headers. Dates in <code className="rounded bg-slate-800 px-1.5 py-0.5">YYYY‑MM‑DD</code>.
                </li>
                <li className="flex items-start gap-2">
                  <div className="h-1.5 w-1.5 mt-1.5 rounded-full bg-slate-600" />
                  The file will be validated and imported automatically upon saving.
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Technical Explanation Textarea */}
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-2">
            Technical Explanation <span className="text-rose-500">*</span>
          </label>
          <textarea
            value={explanation}
            onChange={(e) => setExplanation(e.target.value)}
            rows={6}
            placeholder="Describe the tactical concept, key movements, data insights, and coaching points. Use Markdown for formatting."
            className="w-full rounded-xl border border-slate-700 bg-slate-900 px-5 py-4 text-white placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 resize-none"
            required
          />
          <div className="mt-3 flex justify-between text-sm text-slate-500">
            <span>Supports Markdown formatting (headings, lists, code).</span>
            <span>{explanation.length}/5000 characters</span>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-between pt-6 border-t border-slate-800">
          <div className="text-sm text-slate-500">
            All fields marked with <span className="text-rose-500">*</span> are required.
            The exercise will be visible after moderation.
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-3 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-800 px-8 py-4 text-lg font-bold text-white shadow-2xl hover:from-emerald-500 hover:to-emerald-700 disabled:opacity-70 disabled:cursor-not-allowed transition-all duration-300"
          >
            {isSubmitting ? (
              <>
                <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Saving...
              </>
            ) : (
              <>
                <Save className="h-5 w-5" />
                Save Exercise
              </>
            )}
          </button>
        </div>
      </form>

      {/* Helper note */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-800">
            <FileText className="h-5 w-5 text-slate-400" />
          </div>
          <div>
            <h4 className="font-bold text-white">About Exercise Content</h4>
            <p className="mt-2 text-sm text-slate-400">
              Exercises are stored in the central database and can be linked to specific matches, players, or tactical
              patterns. Use the CSV import to attach quantitative data that supports your analysis. The animation URL
              will be embedded in the public exercise page for interactive visualisation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}