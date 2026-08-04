// Admin Media Library Page
import { useState, useEffect } from "react";
import { adminCoursesAPI } from "../../api/lms";
import { Plus, Trash2, Upload, Image, Video, File, Search, Filter, X } from "lucide-react";

interface MediaAsset {
  id: number;
  filename: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  url: string;
  created_at: string;
}

export default function AdminMediaLibraryPage() {
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    try {
      const data = await adminCoursesAPI.list();
      // Mock data for now
      setAssets([]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploading(true);
    setUploadProgress(0);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
    
    // Would call media API here in production
    setTimeout(() => {
      setUploading(false);
      setUploadProgress(0);
    }, 2000);
  };

  const getIcon = (mimeType: string) => {
    if (mimeType.startsWith("video/")) return <Video className="w-8 h-8 text-blue-500" />;
    if (mimeType.startsWith("image/")) return <Image className="w-8 h-8 text-green-500" />;
    return <File className="w-8 h-8 text-gray-500" />;
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Media Library</h1>
          <p className="text-gray-600">Manage uploaded files</p>
        </div>
        
        <label className="flex items-center gap-2 px-4 py-2 bg-navy-600 text-white rounded-lg cursor-pointer hover:bg-navy-700">
          <Upload className="w-4 h-4" />
          Upload File
          <input 
            type="file" 
            className="hidden" 
            accept="video/*,image/*,application/pdf"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
      </div>

      {uploading && (
        <div className="mb-6 p-4 bg-navy-50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-navy-600 transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <span className="text-sm">{uploadProgress}%</span>
          </div>
        </div>
      )}

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setFilter("all")}
          className={`px-3 py-1.5 rounded-lg text-sm ${
            filter === "all" ? "bg-navy-100 text-navy-700" : "bg-gray-100"
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter("video")}
          className={`px-3 py-1.5 rounded-lg text-sm ${
            filter === "video" ? "bg-navy-100 text-navy-700" : "bg-gray-100"
          }`}
        >
          Videos
        </button>
        <button
          onClick={() => setFilter("image")}
          className={`px-3 py-1.5 rounded-lg text-sm ${
            filter === "image" ? "bg-navy-100 text-navy-700" : "bg-gray-100"
          }`}
        >
          Images
        </button>
        <button
          onClick={() => setFilter("document")}
          className={`px-3 py-1.5 rounded-lg text-sm ${
            filter === "document" ? "bg-navy-100 text-navy-700" : "bg-gray-100"
          }`}
        >
          Documents
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : assets.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>No files uploaded yet</p>
          <p className="text-sm">Upload videos, images, or documents</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {assets.map(asset => (
            <div 
              key={asset.id}
              className="group relative bg-white rounded-lg border overflow-hidden hover:border-navy-300"
            >
              <div className="aspect-square flex items-center justify-center bg-gray-50">
                {getIcon(asset.mime_type)}
              </div>
              <div className="p-2">
                <p className="text-sm truncate">{asset.original_filename}</p>
                <p className="text-xs text-gray-500">{formatSize(asset.size_bytes)}</p>
              </div>
              <button
                className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}