import React, { useState } from 'react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { FaFolderOpen, FaFileAlt, FaUpload } from 'react-icons/fa';
import axios from 'axios';

const FileSystem: React.FC = () => {
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [zipName, setZipName] = useState<string>('');
  const [zipId, setZipId] = useState<string>('');
  const [files, setFiles] = useState<string[]>([]); // List of file paths
  const [selected, setSelected] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  // Upload zip to backend and fetch file list
  const handleZipUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setZipFile(file);
      setZipName(file.name);
      setFiles([]);
      setSelected(null);
      setResult(null);
      setError(null);
      setZipId('');
      setUploading(true);
      try {
        // 1. Upload zip
        const formData = new FormData();
        formData.append('file', file);
        const uploadRes = await axios.post('http://localhost:8000/upload-zip', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        const id = uploadRes.data.zip_filename;
        console.log("I am id: ", id)
        setZipId(id);
        // 2. Fetch file list
        const listRes = await axios.get(`http://localhost:8000/list-files/${id}`);
        setFiles(listRes.data.files || []);
      } catch (err: any) {
        setError('Failed to upload or list files.');
      } finally {
        setUploading(false);
      }
    }
  };

  const handleSelect = (path: string) => {
    setSelected(path);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!zipId || !selected || !prompt.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('zip_filename', zipId);
      formData.append('file_path', selected);
      formData.append('prompt', prompt);
      const res = await axios.post('http://localhost:8000/agent-file', formData);
      setResult(res.data.result);
    } catch (err: any) {
      setError('Error contacting backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-10 w-full max-w-4xl mx-auto py-12 px-2">
      {/* File upload and file tree */}
      <div className="w-full md:w-1/3">
        <Card className="bg-white/20 backdrop-blur-lg border border-white/30 shadow-2xl rounded-2xl">
          <CardContent className="py-6 px-5">
            <div className="flex items-center gap-2 text-lg font-bold text-indigo-300 mb-4">
              <FaFolderOpen className="text-indigo-400 text-xl" />
              Upload Folder <span className="text-xs text-slate-300">(.zip)</span>
            </div>
            <label className={`flex items-center gap-2 cursor-pointer px-4 py-2 rounded-lg shadow transition mb-4 w-fit font-medium ${uploading ? 'bg-indigo-300 text-white' : 'bg-indigo-600/90 hover:bg-indigo-700 text-white active:scale-95'}`}>
              <FaUpload className="text-lg" />
              <span>{uploading ? 'Uploading...' : 'Choose Zip'}</span>
              <input type="file" accept=".zip" onChange={handleZipUpload} className="hidden" disabled={uploading} />
            </label>
            {zipId && (
              <div className="mt-2">
                <div className="flex items-center gap-2 font-semibold text-indigo-200 mb-2">
                  <FaFolderOpen className="text-indigo-300" />
                  <span className="underline underline-offset-2">{zipName}</span>
                </div>
                <ul className="ml-2 space-y-1 mt-2">
                  {files.length === 0 && (
                    <li className="text-indigo-300 italic text-sm">No files found in zip.</li>
                  )}
                  {files.map(file => (
                    <li key={file}>
                      <button
                        className={`flex items-center gap-2 text-left w-full px-3 py-2 rounded-lg transition-all text-base font-medium border border-transparent focus:outline-none focus:ring-2 focus:ring-indigo-400/40
                          ${selected === file
                            ? 'bg-indigo-500/90 text-white border-indigo-400 shadow-lg scale-[1.03]'
                            : 'text-indigo-200 hover:bg-indigo-100/60 hover:text-indigo-900 hover:border-indigo-300 active:scale-95'}
                        `}
                        onClick={() => handleSelect(file)}
                      >
                        <FaFileAlt className="text-indigo-300" />
                        {file}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      {/* Prompt and result */}
      <div className="flex-1">
        <Card className="bg-white/20 backdrop-blur-lg border border-white/30 shadow-2xl rounded-2xl">
          <CardContent className="py-8 px-7">
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
              <div>
                <div className="mb-1 text-slate-200 font-semibold text-base flex items-center gap-2">
                  <FaFileAlt className="text-indigo-300" />
                  Selected File:
                </div>
                <div className={`mb-2 font-mono text-sm ${selected ? 'text-indigo-200' : 'text-indigo-400'}`}
                  style={{ minHeight: 24 }}>
                  {selected ? `${zipName} / ${selected}` : 'No file selected'}
                </div>
              </div>
              <Input
                className="text-base px-4 py-3 rounded-lg border border-indigo-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-300/40 bg-white/60 placeholder:text-indigo-400"
                placeholder="Enter your prompt..."
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                disabled={!selected || loading}
              />
              <Button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-lg font-semibold py-3 rounded-lg shadow transition disabled:opacity-60 active:scale-95"
                disabled={!zipId || !selected || !prompt.trim() || loading}
              >
                {loading ? 'Processing...' : 'Send to Agent'}
              </Button>
            </form>
            {result && (
              <div className="mt-8 p-5 bg-green-50/80 border border-green-200 rounded-lg text-green-900 whitespace-pre-wrap shadow animate-fade-in">
                <div className="font-semibold mb-1">Agent Result:</div>
                {result}
              </div>
            )}
            {error && (
              <div className="mt-8 p-5 bg-red-50/80 border border-red-200 rounded-lg text-red-900 shadow animate-fade-in">
                {error}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FileSystem; 