"use client";

import { CreateReadingForm } from "./_components/create-reading-form";
import { useCreateReadingForm } from "./_components/use-create-reading-form";

export const CreateReading = () => {
  const form = useCreateReadingForm();

  return (
    <CreateReadingForm
      error={form.error}
      isPending={form.isPending}
      isSuccess={form.isSuccess}
      onFileChange={form.handleFileChange}
      onSubmit={form.handleSubmit}
      onTextChange={form.setText}
      onVendorChange={form.setVendor}
      onVoiceChange={form.setVoice}
      readingId={form.readingId}
      state={form.state}
    />
  );
};
