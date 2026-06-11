// app/static/script.js

const LIMITS = {
    titleMin: 3,
    titleMax: 120,
    descriptionMin: 10,
    descriptionMax: 2000,
    maxThumbnailBytes: 5 * 1024 * 1024,
    allowedTypes: ["image/jpeg", "image/png", "image/webp", "image/gif"],
}

const form = document.getElementById("predict-form")
const submitBtn = document.getElementById("submit-btn")
const btnLabel = submitBtn.querySelector(".btn-label")
const btnSpinner = submitBtn.querySelector(".btn-spinner")
const resultsSection = document.getElementById("results-section")
const resultsContent = document.getElementById("results-content")
const globalError = document.getElementById("global-error")
const globalErrorText = document.getElementById("global-error-text")

const thumbnailInput = document.getElementById("thumbnail")
const thumbnailZone = document.getElementById("thumbnail-zone")
const thumbnailEmpty = document.getElementById("thumbnail-empty")
const thumbnailPreview = document.getElementById("thumbnail-preview")
const thumbnailImg = document.getElementById("thumbnail-img")
const thumbnailRemove = document.getElementById("thumbnail-remove")

const slider = document.getElementById("num_extra_images")
const sliderValue = document.getElementById("slider-value")

let previewUrl = null

// ── Slider ───────────────────────────────────────────────────

slider.addEventListener("input", () => {
    sliderValue.textContent = slider.value
})

// ── Thumbnail preview ──────────────────────────────────────

function clearThumbnail() {
    if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
        previewUrl = null
    }
    thumbnailInput.value = ""
    thumbnailImg.src = ""
    thumbnailPreview.hidden = true
    thumbnailEmpty.hidden = false
    thumbnailZone.classList.remove("thumbnail-zone--has-image")
}

function setThumbnailPreview(file) {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    previewUrl = URL.createObjectURL(file)
    thumbnailImg.src = previewUrl
    thumbnailPreview.hidden = false
    thumbnailEmpty.hidden = true
    thumbnailZone.classList.add("thumbnail-zone--has-image")
}

thumbnailInput.addEventListener("change", () => {
    const file = thumbnailInput.files[0]
    if (file) {
        setThumbnailPreview(file)
        clearFieldError("thumbnail")
    }
})

thumbnailRemove.addEventListener("click", (e) => {
    e.preventDefault()
    e.stopPropagation()
    clearThumbnail()
})

;["dragenter", "dragover"].forEach((evt) => {
    thumbnailZone.addEventListener(evt, (e) => {
        e.preventDefault()
        thumbnailZone.classList.add("thumbnail-zone--dragover")
    })
})

;["dragleave", "drop"].forEach((evt) => {
    thumbnailZone.addEventListener(evt, (e) => {
        e.preventDefault()
        thumbnailZone.classList.remove("thumbnail-zone--dragover")
    })
})

thumbnailZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0]
    if (!file) return

    const dt = new DataTransfer()
    dt.items.add(file)
    thumbnailInput.files = dt.files
    setThumbnailPreview(file)
    clearFieldError("thumbnail")
})

// ── Validation ───────────────────────────────────────────────

function getFieldEl(name) {
    return document.querySelector(`[data-field="${name}"]`)
}

function showFieldError(name, message) {
    const field = getFieldEl(name)
    if (!field) return
    field.classList.add("field--invalid")
    const err = field.querySelector(".field-error")
    err.textContent = message
    err.hidden = false
}

function clearFieldError(name) {
    const field = getFieldEl(name)
    if (!field) return
    field.classList.remove("field--invalid")
    const err = field.querySelector(".field-error")
    err.textContent = ""
    err.hidden = true
}

function clearAllErrors() {
    document.querySelectorAll("[data-field]").forEach((field) => {
        field.classList.remove("field--invalid")
        const err = field.querySelector(".field-error")
        if (err) {
            err.textContent = ""
            err.hidden = true
        }
    })
    globalError.hidden = true
}

function validateClient() {
    clearAllErrors()
    const errors = {}

    const title = form.title.value.trim()
    if (title.length < LIMITS.titleMin) {
        errors.title = `Title must be at least ${LIMITS.titleMin} characters.`
    } else if (title.length > LIMITS.titleMax) {
        errors.title = `Title must be at most ${LIMITS.titleMax} characters.`
    }

    const description = form.description.value.trim()
    if (description.length < LIMITS.descriptionMin) {
        errors.description = `Description must be at least ${LIMITS.descriptionMin} characters.`
    } else if (description.length > LIMITS.descriptionMax) {
        errors.description = `Description must be at most ${LIMITS.descriptionMax} characters.`
    }

    const file = thumbnailInput.files[0]
    if (!file) {
        errors.thumbnail = "Thumbnail image is required."
    } else {
        if (!LIMITS.allowedTypes.includes(file.type)) {
            errors.thumbnail = "Thumbnail must be a JPEG, PNG, WebP, or GIF image."
        } else if (file.size > LIMITS.maxThumbnailBytes) {
            errors.thumbnail = "Thumbnail must be 5 MB or smaller."
        }
    }

    const extra = parseInt(slider.value, 10)
    if (extra < 0 || extra > 3) {
        errors.num_extra_images = "Additional images must be between 0 and 3."
    }

    for (const [name, message] of Object.entries(errors)) {
        showFieldError(name, message)
    }

    return Object.keys(errors).length === 0
}

// ── Form reset ───────────────────────────────────────────────

form.addEventListener("reset", () => {
    setTimeout(() => {
        clearThumbnail()
        sliderValue.textContent = "0"
        clearAllErrors()
        resultsSection.hidden = true
    }, 0)
})

// ── Submit ───────────────────────────────────────────────────

form.addEventListener("submit", async (e) => {
    e.preventDefault()

    if (!validateClient()) {
        const firstInvalid = document.querySelector(".field--invalid")
        if (firstInvalid) firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" })
        return
    }

    setLoading(true)
    resultsSection.hidden = true
    globalError.hidden = true

    const data = new FormData()
    data.append("title", form.title.value.trim())
    data.append("description", form.description.value.trim())
    data.append("tags", form.tags.value.trim())
    data.append("has_video", form.has_video.checked ? "1" : "0")
    data.append("num_extra_images", slider.value)
    data.append("thumbnail", thumbnailInput.files[0])

    try {
        const response = await fetch("/predict", { method: "POST", body: data })
        const result = await response.json()

        if (!response.ok) {
            if (result.errors) {
                for (const [name, message] of Object.entries(result.errors)) {
                    showFieldError(name, message)
                }
                const firstInvalid = document.querySelector(".field--invalid")
                if (firstInvalid) firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" })
            } else {
                showGlobalError(result.detail || "Something went wrong. Please try again.")
            }
            return
        }

        renderResults(result)
        resultsSection.hidden = false
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" })
    } catch {
        showGlobalError("Could not reach the server. Make sure the app is running.")
    } finally {
        setLoading(false)
    }
})

function setLoading(loading) {
    submitBtn.disabled = loading
    btnSpinner.hidden = !loading
    btnLabel.textContent = loading ? "Analyzing…" : "Run prediction"
}

function showGlobalError(message) {
    globalErrorText.textContent = message
    globalError.hidden = false
    globalError.scrollIntoView({ behavior: "smooth", block: "center" })
}

// ── Results rendering ────────────────────────────────────────

function formatNumber(n) {
    return Math.round(n).toLocaleString("en-US")
}

function humanizeFeature(feature) {
    if (feature.startsWith("tag_")) {
        return feature.slice(4).replace(/\b\w/g, (c) => c.toUpperCase())
    }
    return feature.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

function describeFactor(feature) {
    if (feature.startsWith("tag_")) {
        const tag = feature.slice(4)
        return `Having the "${tag}" tag on your listing`
    }
    if (feature === "has_video") return "Including a promotional video"
    if (feature === "num_extra_images") return "Number of additional gallery images"
    return humanizeFeature(feature)
}

function renderResults(data) {
    const pred = data.prediction
    const cmp = data.comparison || {}
    const topPct = cmp.percentile != null ? 100 - cmp.percentile : null

    const maxBar = Math.max(pred, cmp.mean || 0, cmp.median || 0, cmp.p75 || 0, cmp.p90 || 0, 1)

    function barWidth(value) {
        return `${Math.min(100, (value / maxBar) * 100).toFixed(1)}%`
    }

    const factorsHtml = (data.top_factors || [])
        .map((f) => {
            const positive = f.impact > 0
            const maxImpact = Math.max(...data.top_factors.map((x) => Math.abs(x.impact)), 0.001)
            const barPct = (Math.abs(f.impact) / maxImpact) * 100
            const sign = positive ? "+" : ""
            return `
                <div class="factor-item">
                    <span class="factor-name">${describeFactor(f.feature)}</span>
                    <span class="factor-impact factor-impact--${positive ? "positive" : "negative"}">${sign}${f.impact.toFixed(3)}</span>
                    <div class="factor-bar-wrap">
                        <div class="factor-bar" style="width:${barPct}%;background:${positive ? "var(--positive)" : "var(--negative)"}"></div>
                    </div>
                </div>`
        })
        .join("")

    resultsContent.innerHTML = `
        <div class="result-hero">
            <p class="result-hero-label">Estimated peak concurrent players</p>
            <p class="result-hero-value">${formatNumber(pred)}</p>
            ${topPct != null ? `<p class="result-hero-sub">Ranks in the top ${topPct}% of islands in our training data</p>` : ""}
        </div>

        <div class="result-grid">
            <div class="result-stat">
                <p class="result-stat-label">Thumbnail impact</p>
                <p class="result-stat-value">${data.thumbnail_score.toFixed(2)}</p>
                <p class="result-stat-desc">How much your thumbnail image influenced the prediction (SHAP magnitude)</p>
            </div>
            <div class="result-stat">
                <p class="result-stat-label">Text impact</p>
                <p class="result-stat-value">${data.text_score.toFixed(2)}</p>
                <p class="result-stat-desc">Combined influence of your title and description</p>
            </div>
            <div class="result-stat">
                <p class="result-stat-label">Metadata impact</p>
                <p class="result-stat-value">${data.metadata_score.toFixed(2)}</p>
                <p class="result-stat-desc">Influence from tags, video flag, and gallery image count</p>
            </div>
        </div>

        ${cmp.mean ? `
        <p class="result-section-title">How you compare to the dataset</p>
        <div class="comparison-bars">
            <div class="comparison-row">
                <span>Your island</span>
                <div class="comparison-bar-track"><div class="comparison-bar-fill comparison-bar-fill--you" style="width:${barWidth(pred)}"></div></div>
                <span>${formatNumber(pred)}</span>
            </div>
            <div class="comparison-row">
                <span>Average</span>
                <div class="comparison-bar-track"><div class="comparison-bar-fill" style="width:${barWidth(cmp.mean)}"></div></div>
                <span>${formatNumber(cmp.mean)}</span>
            </div>
            <div class="comparison-row">
                <span>Median</span>
                <div class="comparison-bar-track"><div class="comparison-bar-fill" style="width:${barWidth(cmp.median)}"></div></div>
                <span>${formatNumber(cmp.median)}</span>
            </div>
            <div class="comparison-row">
                <span>75th %ile</span>
                <div class="comparison-bar-track"><div class="comparison-bar-fill" style="width:${barWidth(cmp.p75)}"></div></div>
                <span>${formatNumber(cmp.p75)}</span>
            </div>
            <div class="comparison-row">
                <span>90th %ile</span>
                <div class="comparison-bar-track"><div class="comparison-bar-fill" style="width:${barWidth(cmp.p90)}"></div></div>
                <span>${formatNumber(cmp.p90)}</span>
            </div>
        </div>
        <p class="result-stat-desc" style="margin-bottom:1.75rem">
            Your estimate is <strong>${cmp.vs_mean?.toFixed(2)}×</strong> the dataset average
            and <strong>${cmp.vs_median?.toFixed(2)}×</strong> the median.
        </p>
        ` : ""}

        <p class="result-section-title">Top factors affecting your prediction</p>
        <p class="field-hint" style="margin-bottom:0.75rem">
            Positive values push the estimate up; negative values pull it down.
            Only human-readable factors are shown (raw embedding dimensions are hidden).
        </p>
        <div class="factors-list">${factorsHtml || "<p class='field-hint'>No notable metadata factors detected.</p>"}</div>
    `
}
