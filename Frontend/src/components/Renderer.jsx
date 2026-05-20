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
  const isSalesOrder = key_name === "SalesOrder";

  // const Backend_url = "https://invoice-scanner-7hgz.vercel.app/";        
  const Backend_url = "http://127.0.0.1:8000/";

  useEffect(() => {

    if (!key_name) {
      navigate("/select");
    }

  }, []);

  // ─────────────────────────────────────────────
  // File Selection
  // ─────────────────────────────────────────────
  const handleFileChange = (e) => {

    const selected = e.target.files?.[0];

    if (!selected) return;

    // Sales Order Validation
    if (isSalesOrder) {

      const validMimeType =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

      if (selected.type !== validMimeType) {

        toast.error("Only .xlsx files allowed ❌");

        return;
      }
    }

    setFile(selected);

    // CSV
    if (isBank) {

      setPreview(null);
    }

    // XLSX
    else if (isSalesOrder) {

      setPreview("XLSX");
    }

    // PDF
    else if (selected.type === "application/pdf") {

      setPreview("PDF");
    }

    // Image
    else {

      setPreview(
        URL.createObjectURL(selected)
      );
    }

    e.target.value = "";
  };

  // ─────────────────────────────────────────────
  // Open File Picker
  // ─────────────────────────────────────────────
  const openFilePicker = () => {

    if (!loading) {
      fileInputRef.current?.click();
    }
  };

  // ─────────────────────────────────────────────
  // Open Camera
  // ─────────────────────────────────────────────
  const openCamera = () => {

    if (!loading) {
      cameraInputRef.current?.click();
    }
  };

  // ─────────────────────────────────────────────
  // Upload
  // ─────────────────────────────────────────────
  const handleSend = async () => {

    if (!file) return;

    setLoading(true);

    const formData = new FormData();

    formData.append("file", file);

    if (!isBank && !isSalesOrder) {

      formData.append(
        "KeyName",
        key_name || ""
      );
    }

    let endpoint = "";

    // CSV
    if (isBank) {

      endpoint = `${Backend_url}Render-CSV/`;
    }

    // Sales Order XLSX
    else if (isSalesOrder) {

      endpoint = `${Backend_url}Sales-Order/`;
    }

    // PDF
    else if (file.type === "application/pdf") {

      endpoint = `${Backend_url}Render-PDF/`;
    }

    // Image
    else {

      endpoint = `${Backend_url}Render/`;
    }

    try {

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      console.log(data);

      if (!response.ok || !data.success) {

        throw new Error(
          data.message || "Upload Failed"
        );
      }

      toast.success(

        isBank
          ? "CSV Uploaded Successfully ✅"
          : isSalesOrder
            ? "Sales Order Uploaded Successfully ✅"
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
          : isSalesOrder
            ? "Failed To Upload Sales Order ❌"
            : file.type === "application/pdf"
              ? "Failed To Upload PDF ❌"
              : "Failed To Upload Image ❌"
      );

    } finally {

      setLoading(false);
    }
  };

  // ─────────────────────────────────────────────
  // Bank CSV UI
  // ─────────────────────────────────────────────
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

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileChange}
            className="hidden"
            disabled={loading}
          />

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

                <p className="font-semibold text-gray-700 break-all">
                  {file.name}
                </p>

                <p className="text-xs text-gray-400">
                  {(file.size / 1024).toFixed(1)} KB
                </p>

              </div>

            ) : (

              <div className="flex flex-col items-center gap-2 text-gray-400">

                <p className="font-medium">
                  Click to select CSV file
                </p>

                <p className="text-xs">
                  Only .csv files are accepted
                </p>

              </div>
            )}
          </div>

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

  // ─────────────────────────────────────────────
  // Main Upload UI
  // ─────────────────────────────────────────────
  return (

    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">

      <Toaster position="top-right" reverseOrder={false} />

      <div className="bg-white shadow-xl rounded-2xl p-6 w-full max-w-md">

        <h1 className="text-2xl font-bold text-center mb-6">

          {
            isSalesOrder
              ? "Upload Sales Order XLSX"
              : <>Upload or Capture Image/PDF of <br /> ({key_name} invoice)</>
          }

        </h1>

        {/* File Picker */}
        <input
          ref={fileInputRef}
          type="file"
          accept={
            isSalesOrder
              ? ".xlsx"
              : "image/*,.pdf,application/pdf"
          }
          onChange={handleFileChange}
          onClick={(e) => { e.target.value = null; }}
          className="hidden"
          disabled={loading}
        />

        {/* Camera */}
        {
          !isSalesOrder && (

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
          )
        }

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

            {
              isSalesOrder
                ? "Upload XLSX"
                : "Upload Image / PDF"
            }

          </button>

          {
            !isSalesOrder && (

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
            )
          }
        </div>

        {/* Preview */}
        {preview && (

          <div className="mt-6">

            {(preview === "PDF" || preview === "XLSX") ? (

              <div className="border rounded-xl p-6 flex flex-col items-center justify-center bg-gray-50">

                <p className="mt-3 font-semibold break-all">
                  {file?.name}
                </p>

                <p className="text-sm text-gray-500">

                  {
                    preview === "PDF"
                      ? "PDF Selected"
                      : "Excel File Selected"
                  }

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

        {/* Upload Button */}
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