"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const API_ROOT = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function EditorPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [content, setContent] = useState("");
  const [heroImage, setHeroImage] = useState("");
  const [category, setCategory] = useState<string>("");
  const [league, setLeague] = useState<string>("");
  const [team, setTeam] = useState<string>("");
  const [isFeatured, setIsFeatured] = useState<boolean>(false);
  const [matchId, setMatchId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const url = `${API_ROOT}/api/admin/articles`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          author,
          content,
          hero_image: heroImage || null,
          category: category || null,
          league: league || null,
          team: team || null,
          is_featured: isFeatured,
          match_id: matchId,
        }),
      });

      if (!response.ok) {
        // Check if response is JSON
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const err = await response.json();
          throw new Error(err.detail || `HTTP ${response.status}`);
        } else {
          const text = await response.text();
          throw new Error(`HTTP ${response.status}: ${text.slice(0, 100)}`);
        }
      }

      // Parse JSON only if content-type indicates JSON
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const article = await response.json();
        setSuccess(true);
        // Reset form
        setTitle("");
        setAuthor("");
        setContent("");
        setHeroImage("");
        setCategory("");
        setLeague("");
        setTeam("");
        setIsFeatured(false);
        setMatchId(null);
        // Optionally redirect to the article page
        // router.push(`/article/${article.slug}`);
      } else {
        throw new Error("Received non-JSON response from server");
      }
    } catch (err: any) {
      setError(err.message || "Failed to save article");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Editorial CMS</h1>
        <p className="text-slate-400 mt-2">
          Write and publish articles to the xPalermoStat blog.
        </p>
      </div>

      {success && (
        <div className="mb-6 p-4 bg-emerald-900/30 border border-emerald-700 rounded-lg">
          <p className="text-emerald-300">
            Article saved successfully! You can now view it on the blog.
          </p>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg">
          <p className="text-red-300">Error: {error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl">
        <div>
          <label className="block text-slate-300 mb-2 font-medium">
            Title *
          </label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-palermo-pink focus:border-transparent"
            placeholder="Enter article title"
          />
        </div>

        <div>
          <label className="block text-slate-300 mb-2 font-medium">
            Author *
          </label>
          <input
            type="text"
            required
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-palermo-pink focus:border-transparent"
            placeholder="Author name"
          />
        </div>

        <div>
          <label className="block text-slate-300 mb-2 font-medium">
            Hero Image URL (optional)
          </label>
          <input
            type="url"
            value={heroImage}
            onChange={(e) => setHeroImage(e.target.value)}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-palermo-pink focus:border-transparent"
            placeholder="https://example.com/image.jpg"
          />
        </div>

        <div>
          <label className="block text-slate-300 mb-2 font-medium">
            Category (optional)
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-palermo-pink focus:border-transparent"
          >
            <option value="">Select a category</option>
            <option value="Analysis">Analysis</option>
            <option value="News">News</option>
            <option value="Report">Report</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-300 mb-2 font-medium">
            League (optional)
          </label>
          <select
            value={league}
            onChange={(e) => setLeague(e.target.value)}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-palermo-pink focus:border-transparent"
          >
            <option value="">Select a league</option>
            <option value="Serie A">Serie A</option>
            <option value="Premier League">Premier League</option>
            <option value="Serie B">Serie B</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-300 mb-2 font-medium">
            Team (optional)
          </label>
          <input
            type="text"
            value={team}
            onChange={(e) => setTeam(e.target.value)}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-palermo-pink focus:border-transparent"
            placeholder="e.g., Palermo"
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_featured"
            checked={isFeatured}
            onChange={(e) => setIsFeatured(e.target.checked)}
            className="mr-3 h-5 w-5 accent-palermo-pink"
          />
          <label htmlFor="is_featured" className="text-slate-300">
            Feature this article on the homepage
          </label>
        </div>

        <div>
          <label className="block text-slate-300 mb-2 font-medium">
            Match ID (optional)
          </label>
          <input
            type="number"
            value={matchId ?? ''}
            onChange={(e) => setMatchId(e.target.value ? parseInt(e.target.value) : null)}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-palermo-pink focus:border-transparent"
            placeholder="e.g., 27362"
          />
        </div>

        <div>
          <label className="block text-slate-300 mb-2 font-medium">
            Content *
          </label>
          <textarea
            required
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={15}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-palermo-pink focus:border-transparent font-mono"
            placeholder="Write your article content (Markdown supported)"
          />
          <p className="text-slate-500 text-sm mt-2">
            Supports HTML/Markdown. Use plain text for now.
          </p>
        </div>

        <div className="flex items-center justify-between pt-6 border-t border-slate-800">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-6 py-3 border border-slate-700 text-slate-300 rounded-lg hover:bg-slate-800 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-3 bg-palermo-pink text-white font-bold rounded-lg hover:bg-pink-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Publishing..." : "Publish Article"}
          </button>
        </div>
      </form>

      <div className="mt-12 pt-8 border-t border-slate-800">
        <h2 className="text-xl font-bold text-white mb-4">Recent Articles</h2>
        <p className="text-slate-400">
          After publishing, articles will appear on the blog homepage and can be
          accessed via their slug.
        </p>
        <div className="mt-6">
          <button
            onClick={() => router.push("/admin")}
            className="text-palermo-pink hover:underline"
          >
            ← Back to Admin Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}