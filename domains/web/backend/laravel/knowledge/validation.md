# Laravel Validation Best Practices

- Gunakan `$request->validate()` di controller.
- Aturan umum: `'email' => 'required|email'`
- Kustom pesan error: `'email.required' => 'Email wajib diisi'`
- Validasi array: `'items.*.name' => 'required'`