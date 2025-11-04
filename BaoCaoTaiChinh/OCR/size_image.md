**Kỳ vọng của model dots.ocr về ảnh đầu vào:**

* **Định dạng ảnh:** Ảnh đầu vào phổ biến là PNG/JPG (Xem ví dụ trong docs: `demo/demo_image1.jpg`).
* **Kích thước/độ phân giải ảnh:**
  * Model được tối ưu cho ảnh có **độ phân giải dưới 11,289,600 pixels** (ví dụ: ~3360x3360px hoặc nhỏ hơn).
  * Nếu ảnh độ phân giải/thông tin bị nén, **nên upsample lên DPI 200** (đặc biệt với ảnh chuyển từ PDF bằng `pdf2image`).
* **Số chiều và mode:**
  * Cần đúng số chiều/mode (thường là RGB, dtype uint8 hoặc float32 chuẩn hóa sau khi load ảnh).
* **Không nên chứa quá nhiều ký tự đặc biệt hoặc đặc trưng không tự nhiên (nhiều dấu _ hoặc ...)** — sẽ làm model dễ fail hoặc lặp output.
* **Bố cục:** Một ảnh mỗi lần inference cho task nhận diện layout; nếu batch, tất cả các ảnh của batch phải cùng shape/format.
* **Bắt buộc đúng format đầu vào qua base64 hoặc tensor (nếu gọi API qua client, cần base64 encoded)** .

**Trích dẫn docs:**

> *Try enlarging the image or increasing the PDF parsing DPI (a setting of 200 is recommended). However, please note that the model performs optimally on images with a resolution under 11289600 pixels.*
>
> *Please use a directory name without periods (e.g., DotsOCR instead of dots.ocr) for the model save path. This is a temporary workaround...*
>
> *The model may fail to parse under certain conditions (nhiều special chars, ratio char/pixel quá lớn...)*

**Tóm lại:**

* **Kiểm tra size và mode ảnh:**

  Nên dùng PIL kiểm tra trước khi encode base64:

  <pre class="not-prose w-full rounded font-mono text-sm font-extralight"><div class="codeWrapper text-light selection:text-super selection:bg-super/10 my-md relative flex flex-col rounded font-mono text-sm font-normal bg-subtler"><div class="translate-y-xs -translate-x-xs bottom-xl mb-xl flex h-0 items-start justify-end md:sticky md:top-[100px]"><div class="overflow-hidden rounded-full border-subtlest ring-subtlest divide-subtlest bg-base"><div class="border-subtlest ring-subtlest divide-subtlest bg-subtler"><button data-testid="toggle-wrap-code-button" aria-label="Wrap lines" type="button" class="focus-visible:bg-subtle hover:bg-subtle text-quiet  hover:text-foreground dark:hover:bg-subtle font-sans focus:outline-none outline-none outline-transparent transition duration-300 ease-out select-none items-center relative group/button font-semimedium justify-center text-center items-center rounded-full cursor-pointer active:scale-[0.97] active:duration-150 active:ease-outExpo origin-center whitespace-nowrap inline-flex text-sm h-8 aspect-square" data-state="closed"><div class="flex items-center min-w-0 gap-two justify-center"><div class="flex shrink-0 items-center justify-center size-4"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" color="currentColor" class="tabler-icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6l16 0 M4 18l5 0 M4 12h13a3 3 0 0 1 0 6h-4l2 -2m0 4l-2 -2"></path></svg></div></div></button><button data-testid="copy-code-button" aria-label="Copy code" type="button" class="focus-visible:bg-subtle hover:bg-subtle text-quiet  hover:text-foreground dark:hover:bg-subtle font-sans focus:outline-none outline-none outline-transparent transition duration-300 ease-out select-none items-center relative group/button font-semimedium justify-center text-center items-center rounded-full cursor-pointer active:scale-[0.97] active:duration-150 active:ease-outExpo origin-center whitespace-nowrap inline-flex text-sm h-8 aspect-square" data-state="closed"><div class="flex items-center min-w-0 gap-two justify-center"><div class="flex shrink-0 items-center justify-center size-4"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" color="currentColor" class="tabler-icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1"></path></svg></div></div></button></div></div></div><div class="-mt-xl"><div><div data-testid="code-language-indicator" class="text-quiet bg-subtle py-xs px-sm inline-block rounded-br rounded-tl-[3px] font-thin">python</div></div><div><span><code><span class="token token">from</span><span> PIL </span><span class="token token">import</span><span> Image
  </span><span>img </span><span class="token token operator">=</span><span> Image</span><span class="token token punctuation">.</span><span class="token token">open</span><span class="token token punctuation">(</span><span>image_path</span><span class="token token punctuation">)</span><span>
  </span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span>img</span><span class="token token punctuation">.</span><span>size</span><span class="token token punctuation">,</span><span> img</span><span class="token token punctuation">.</span><span>mode</span><span class="token token punctuation">)</span><span>
  </span></code></span></div></div></div></pre>
* **Nếu ảnh quá lớn hoặc quá nhỏ, cần resize/upsample phù hợp** .
* **Chỉ đưa vào 1 ảnh/lần yêu cầu (trừ prompt/batch được config rõ ràng)** .
* **Đúng định dạng PNG/JPG, tối ưu RGB, không bị hỏng file.**

Bạn hãy log các giá trị:

* `img.size`, `img.mode`, `format`, và confirm ảnh có dtype phù hợp.
* Đảm bảo ảnh truyền đúng yêu cầu để tránh lỗi shape cho GPU/model.

Nếu muốn đảm bảo “match” chuẩn input của model, hãy convert ảnh về PNG/JPG, mode RGB, và scale DPI hợp lý trước khi encode hoặc gọi API.

1. [https://github.com/rednote-hilab/dots.ocr](https://github.com/rednote-hilab/dots.ocr)
