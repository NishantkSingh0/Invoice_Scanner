import { useRef, useEffect, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import { useNavigate, useLocation } from "react-router-dom";

export default function UploadImage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const key_name = location.state?.key_name;
  const isBank = key_name === "bank";
  const Backend_url ="http://127.0.0.1:8000/";         // http://127.0.0.1:8000/      or       https://invoice-scanner-7hgz.vercel.app/
  
  useEffect(() => {
    if (!key_name) {
      navigate("/select");
    }
  }, []);

  // ── File Selection ──────────────────────────────────────────────────────────
  const handleFileChange = (e) => {
    const selected = e.target.files && e.target.files[0];
    if (selected) {
      setFile(selected);

      // CSV → no preview
      if (isBank) {
        setPreview(null);
      }
      // PDF Preview
      else if (selected.type === "application/pdf") {
        setPreview("PDF");
      }
      // Image Preview
      else {
        setPreview(URL.createObjectURL(selected));
      }
    }
    e.target.value = "";
  };

  const openFilePicker = () => {
    if (!loading) {
      fileInputRef.current?.click();
    }
  };

  const openCamera = () => {
    if (!loading) {
      cameraInputRef.current?.click();
    }
  };

  // ── Upload ──────────────────────────────────────────────────────────────────
  const handleSend = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    if (!isBank) {
      formData.append("KeyName", key_name || "");
    }
    let endpoint = "";
    if (isBank) {
      endpoint = `${Backend_url}Render-CSV/`;
    }
    else if (file.type === "application/pdf") {
      endpoint = `${Backend_url}Render-PDF/`;
    }
    else {
      endpoint = `${Backend_url}Render/`;
    }

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload Failed: ${errorText}`);
      }
      const data = await response.json();
      console.log(data);
      toast.success(
        isBank
          ? "CSV Uploaded Successfully ✅"
          : file.type === "application/pdf"
            ? "PDF Uploaded Successfully ✅"
            : "Image Uploaded Successfully ✅"
      );
      setFile(null);
      setPreview(null);
    } catch (error) {
      console.error(error);
      toast.error(
        isBank
          ? "Failed To Upload CSV ❌"
          : file.type === "application/pdf"
            ? "Failed To Upload PDF ❌"
            : "Failed To Upload Image ❌"
      );
    } finally {
      setLoading(false);
    }
  };

  // ── Bank CSV UI ─────────────────────────────────────────────────────────────
  if (isBank) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
        <Toaster position="top-right" reverseOrder={false} />

        <div className="bg-white shadow-xl rounded-2xl p-6 w-full max-w-md">
          <h1 className="text-2xl font-bold text-center mb-2">
            Upload Bank Statement
          </h1>
          <p className="text-center text-gray-500 text-sm mb-6">
            Select a CSV file exported from your bank
          </p>
          {/* Hidden CSV Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileChange}
            className="hidden"
            disabled={loading}
          />
          {/* Drop Area */}
          <div
            onClick={openFilePicker}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
              loading
                ? "border-gray-300 bg-gray-50 cursor-not-allowed"
                : "border-blue-400 hover:border-blue-600 hover:bg-blue-50"
            }`}
          >
            {file ? (
              <div className="flex flex-col items-center gap-2">
                <svg
                  className="w-12 h-12 text-blue-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <p className="font-semibold text-gray-700 break-all">
                  {file.name}
                </p>
                <p className="text-xs text-gray-400">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
                {!loading && (
                  <p className="text-xs text-blue-500 mt-1">
                    Click to change file
                  </p>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-gray-400">
                <svg
                  className="w-12 h-12"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                  />
                </svg>
                <p className="font-medium">
                  Click to select CSV file
                </p>
                <p className="text-xs">
                  Only .csv files are accepted
                </p>
              </div>
            )}
          </div>
          {/* Upload Button */}
          <button
            disabled={!file || loading}
            onClick={handleSend}
            className={`w-full mt-6 py-3 rounded-xl text-white font-semibold flex items-center justify-center ${
              file && !loading
                ? "bg-blue-500 hover:bg-blue-600"
                : "bg-gray-400 cursor-not-allowed"
            }`}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Uploading...
              </div>
            ) : (
              "Upload CSV"
            )}
          </button>
        </div>
      </div>
    );
  }

  // ── Image / PDF UI ──────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
      <Toaster position="top-right" reverseOrder={false} />
      <div className="bg-white shadow-xl rounded-2xl p-6 w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6">
          Upload or Capture Image/PDF of <br />
          ({key_name} invoice)
        </h1>
        {/* File Picker */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf,application/pdf"
          onChange={handleFileChange}
          onClick={(e) => { e.target.value = null; }}
          className="hidden"
          disabled={loading}
        />
        {/* Camera */}
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileChange}
          onClick={(e) => { e.target.value = null; }}
          className="hidden"
          disabled={loading}
        />
        <div className="flex gap-4">
          <button
            disabled={loading}
            onClick={openFilePicker}
            className={`flex-1 py-3 rounded-xl text-white ${
              loading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-500 hover:bg-blue-600"
            }`}
          >
            Upload Image / PDF
          </button>
          <button
            disabled={loading}
            onClick={openCamera}
            className={`flex-1 py-3 rounded-xl text-white ${
              loading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-green-500 hover:bg-green-600"
            }`}
          >
            Open Camera
          </button>
        </div>
        {/* Preview */}
        {preview && (
          <div className="mt-6">
            {preview === "PDF" ? (
              <div className="border rounded-xl p-6 flex flex-col items-center justify-center bg-gray-50">
                <svg
                  className="w-16 h-16 text-red-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M7 21h10a2 2 0 002-2V7.414a2 2 0 00-.586-1.414l-4.414-4.414A2 2 0 0012.586 1H7a2 2 0 00-2 2v16a2 2 0 002 2z"
                  />
                </svg>
                <p className="mt-3 font-semibold break-all">
                  {file?.name}
                </p>
                <p className="text-sm text-gray-500">
                  PDF Selected
                </p>

              </div>
            ) : (
              <img
                src={preview}
                alt="Preview"
                className="w-full h-64 object-cover rounded-xl border"
              />
            )}
          </div>
        )}
        {/* Send */}
        <button
          disabled={!file || loading}
          onClick={handleSend}
          className={`w-full mt-6 py-3 rounded-xl text-white font-semibold flex items-center justify-center ${
            file && !loading
              ? "bg-black hover:bg-gray-800"
              : "bg-gray-400 cursor-not-allowed"
          }`}
        >
          {loading ? (
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Uploading...
            </div>
          ) : (
            "Send"
          )}
        </button>
      </div>
    </div>
  );
}