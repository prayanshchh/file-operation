import React, { useState } from 'react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { FaFolderOpen, FaFileAlt, FaUpload, FaRegCopy, FaTimes } from 'react-icons/fa';
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
  const [fileContent, setFileContent] = useState<string>('');
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [customFilePath, setCustomFilePath] = useState('');

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
      setFileContent('');
      setFileError(null);
      try {
        // 1. Upload zip
        const formData = new FormData();
        formData.append('file', file);
        const uploadRes = await axios.post('http://localhost:8000/upload-zip', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        const id = uploadRes.data.zip_filename;
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

  // Fetch file content when a file is selected
  const handleSelect = async (path: string) => {
    setSelected(path);
    setResult(null);
    setError(null);
    setFileContent('');
    setFileError(null);
    if (!zipId) return;
    setFileLoading(true);
    try {
      const res = await axios.get(`http://localhost:8000/file/${zipId}/${encodeURIComponent(path)}`);
      setFileContent(res.data);
    } catch (err: any) {
      setFileError('Failed to fetch file content.');
    } finally {
      setFileLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!zipId || !prompt.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('zip_filename', zipId);
      formData.append('file_path', selected || customFilePath || '');
      formData.append('prompt', prompt);
      const res = await axios.post('http://localhost:8000/agent-file', formData);
      setResult(res.data.result);
    } catch (err: any) {
      setError('Error contacting backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!fileContent) return;
    navigator.clipboard.writeText(fileContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  // Deselect file
  const handleDeselect = () => {
    setSelected(null);
    setFileContent('');
    setFileError(null);
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
                {/* File viewer */}
                {selected && (
                  <div className="mt-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-indigo-400 font-semibold text-sm flex items-center gap-2">
                        <FaFileAlt className="text-indigo-300" />
                        {selected}
                      </span>
                      <div className="flex gap-2">
                        <button
                          className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border border-indigo-200 bg-white/60 hover:bg-indigo-100 text-indigo-700 transition active:scale-95 ${copied ? 'bg-green-100 text-green-700 border-green-300' : ''}`}
                          onClick={handleCopy}
                          type="button"
                          disabled={!fileContent}
                          title="Copy file contents"
                        >
                          <FaRegCopy />
                          {copied ? 'Copied!' : 'Copy'}
                        </button>
                        <button
                          className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border border-red-200 bg-white/60 hover:bg-red-100 text-red-700 transition active:scale-95"
                          onClick={handleDeselect}
                          type="button"
                          title="Deselect file"
                        >
                          <FaTimes />
                          Deselect
                        </button>
                      </div>
                    </div>
                    <div className="bg-slate-900/80 text-green-200 rounded-lg p-3 text-xs font-mono max-h-60 overflow-auto border border-slate-700 shadow-inner transition-all min-h-[60px]">
                      {fileLoading ? (
                        <span className="text-indigo-200 animate-pulse">Loading...</span>
                      ) : fileError ? (
                        <span className="text-red-400">{fileError}</span>
                      ) : fileContent ? (
                        <pre className="whitespace-pre-wrap break-words">{fileContent}</pre>
                      ) : (
                        <span className="text-slate-400">No content to display.</span>
                      )}
                    </div>
                  </div>
                )}
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
                {!selected && (
                  <Input
                    className="text-xs px-3 py-2 rounded border border-indigo-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-300/40 bg-white/60 placeholder:text-indigo-400 mb-2"
                    placeholder="Or enter a file path (e.g. folder/file.txt)"
                    value={customFilePath}
                    onChange={e => setCustomFilePath(e.target.value)}
                    disabled={loading}
                  />
                )}
              </div>
              <Input
                className="text-base px-4 py-3 rounded-lg border border-indigo-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-300/40 bg-white/60 placeholder:text-indigo-400"
                placeholder="Enter your prompt..."
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                disabled={loading}
              />
              <Button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-lg font-semibold py-3 rounded-lg shadow transition disabled:opacity-60 active:scale-95"
                disabled={!zipId || !prompt.trim() || loading}
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