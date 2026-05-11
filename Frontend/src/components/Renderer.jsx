import React, { useRef, useEffect, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import { useNavigate } from "react-router-dom";

export default function UploadImage() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const navigate = useNavigate()
  const Backend_url = "http://127.0.0.1:8000/"                // http://127.0.0.1:8000/      or       https://invoice-scanner-7hgz.vercel.app/

  // Handle Upload
  const handleFileChange = (e) => {
    const file = e.target.files && e.target.files[0];

    if (file) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
    }

    // Reset input value so the same file can be re-selected later
    e.target.value = "";
  };
  useEffect(() => {
  
    if (!location.state?.key_name) {
      navigate("/select");
    }
  
  }, []);

  const openFilePicker = () => {
    if (!loading) {
      fileInputRef.current?.click();
    }
  };

  // Open Camera
  const openCamera = () => {
    if (!loading) {
      cameraInputRef.current?.click();
    }
  };

  // Send Image
  const handleSend = async () => {
    if (!image) return;

    setLoading(true);

    const formData = new FormData();
    formData.append("file", image);

    formData.append(
      "KeyName",
      location.state?.key_name || ""
    );
    try {
      const response = await fetch(`${Backend_url}Render/`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload Failed: ${errorText}`);
      }

      const data = await response.json();

      console.log(data);

      toast.success("Image Uploaded Successfully ✅");

      setLoading(false);
    } catch (error) {
      console.error(error);

      toast.error("Failed To Upload Image ❌");

      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
      {/* Toast */}
      <Toaster position="top-right" reverseOrder={false} />

      <div className="bg-white shadow-xl rounded-2xl p-6 w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6">
          Upload or Capture Image
        </h1>

        {/* Hidden Input for File Upload */}
        <input
          ref={fileInputRef}
          name="file"
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          onClick={(e) => {
            e.target.value = null;
          }}
          className="hidden"
          disabled={loading}
        />

        {/* Hidden Input for Camera */}
        <input
          ref={cameraInputRef}
          name="file"
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileChange}
          onClick={(e) => {
            e.target.value = null;
          }}
          className="hidden"
          disabled={loading}
        />

        <div className="flex gap-4">
          {/* Upload */}
          <button
            disabled={loading}
            onClick={openFilePicker}
            className={`flex-1 py-3 rounded-xl text-white ${
              loading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-500 hover:bg-blue-600"
            }`}
          >
            Upload Image
          </button>

          {/* Camera */}
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
            <img
              src={preview}
              alt="Preview"
              className="w-full h-64 object-cover rounded-xl border"
            />
          </div>
        )}

        {/* Send */}
        <button
          disabled={!image || loading}
          onClick={handleSend}
          className={`w-full mt-6 py-3 rounded-xl text-white font-semibold flex items-center justify-center ${
            image && !loading
              ? "bg-black hover:bg-gray-800"
              : "bg-gray-400 cursor-not-allowed"
          }`}
        >
          {loading ? (
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
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