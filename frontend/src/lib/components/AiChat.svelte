<script lang="ts">
	import { onMount, tick } from "svelte";
	import { Sparkles, X, Send, RotateCcw } from "lucide-svelte";
	import { api } from "$lib/api";

	let { refreshKey = 0 }: { refreshKey?: number } = $props();

	type Msg = { role: "user" | "assistant"; content: string };
	const STORAGE_KEY = "cisco_ai_chat";
	const MAX_KEPT = 20;
	const MAX_SENT = 6; // l'historique envoyé au modèle reste court pour économiser les tokens
	const SUGGESTIONS = ["Quels devoirs ai-je cette semaine ?", "Quel est mon prochain cours ?", "Où ai-je perdu le plus de points ?", "Ajoute un devoir de maths pour vendredi"];

	let ready = $state(false);
	let open = $state(false);
	let messages = $state<Msg[]>([]);
	let input = $state("");
	let loading = $state(false);
	let error = $state("");
	let scroller = $state<HTMLElement | null>(null);

	async function loadStatus() {
		try {
			const s = await api.getAiStatus();
			ready = s.configured && s.verified;
		} catch {
			ready = false;
		}
		if (!ready) open = false;
	}

	$effect(() => {
		refreshKey;
		loadStatus();
	});

	onMount(() => {
		try {
			const saved = sessionStorage.getItem(STORAGE_KEY);
			if (saved) messages = JSON.parse(saved);
		} catch {
			// stockage indisponible : conversation éphémère
		}
	});

	function persist() {
		try {
			sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-MAX_KEPT)));
		} catch {
			// ignore
		}
	}

	async function scrollDown() {
		await tick();
		scroller?.scrollTo({ top: scroller.scrollHeight, behavior: "smooth" });
	}

	async function send(text: string) {
		const question = text.trim();
		if (!question || loading) return;
		error = "";
		input = "";
		messages = [...messages, { role: "user", content: question }];
		loading = true;
		scrollDown();
		try {
			const res = await api.aiChat(messages.slice(-MAX_SENT));
			messages = [...messages, { role: "assistant", content: res.reply }];
			// L'assistant a ajouté un devoir : les listes affichées doivent se rafraîchir
			if (res.tasks_created > 0) window.dispatchEvent(new CustomEvent("cisco:tasks-changed"));
		} catch (e: any) {
			error = e.message || "L'assistant n'a pas pu répondre.";
			// Un échec de clé désactive l'assistant : on relit l'état
			loadStatus();
		} finally {
			loading = false;
			persist();
			scrollDown();
		}
	}

	function reset() {
		messages = [];
		error = "";
		persist();
	}

	function onKeydown(e: KeyboardEvent) {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			send(input);
		} else if (e.key === "Escape") {
			open = false;
		}
	}

	// Rendu minimal et sûr : le texte est échappé, seuls **gras**, listes à puces et paragraphes sont interprétés.
	function render(text: string): string {
		const esc = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
		const inline = (t: string) => t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>");
		let html = "";
		let inList = false;
		for (const raw of esc.split("\n")) {
			const bullet = raw.match(/^\s*[-*•]\s+(.*)$/);
			if (bullet) {
				if (!inList) html += '<ul class="list-disc pl-4 space-y-0.5 my-1">';
				inList = true;
				html += `<li>${inline(bullet[1])}</li>`;
			} else {
				if (inList) html += "</ul>";
				inList = false;
				html += raw.trim() ? `<p>${inline(raw)}</p>` : "";
			}
		}
		return html + (inList ? "</ul>" : "");
	}
</script>

{#if ready}
	{#if !open}
		<button
			type="button"
			onclick={() => {
				open = true;
				scrollDown();
			}}
			aria-label="Ouvrir l'assistant IA"
			title="Assistant IA"
			class="fixed z-40 right-4 bottom-20 md:right-6 md:bottom-6 w-12 h-12 rounded-full bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg flex items-center justify-center cursor-pointer transition-colors"
		>
			<Sparkles class="w-5 h-5" />
		</button>
	{:else}
		<section
			aria-label="Assistant IA"
			class="fixed z-40 right-4 bottom-20 md:right-6 md:bottom-6 w-[calc(100vw-2rem)] sm:w-96 h-[min(34rem,calc(100dvh-7rem))] rounded-xl border border-app-border bg-app-card shadow-2xl flex flex-col overflow-hidden"
		>
			<header class="flex items-center justify-between gap-2 px-4 py-3 border-b border-app-border">
				<div class="flex items-center gap-2 text-sm font-bold text-fg">
					<Sparkles class="w-4 h-4 text-cyan-400" />
					Assistant
				</div>
				<div class="flex items-center gap-1">
					{#if messages.length > 0}
						<button type="button" onclick={reset} title="Nouvelle conversation" aria-label="Nouvelle conversation" class="p-1.5 rounded-md text-muted hover:text-fg hover:bg-app-raised cursor-pointer">
							<RotateCcw class="w-4 h-4" />
						</button>
					{/if}
					<button type="button" onclick={() => (open = false)} title="Fermer" aria-label="Fermer" class="p-1.5 rounded-md text-muted hover:text-fg hover:bg-app-raised cursor-pointer">
						<X class="w-4 h-4" />
					</button>
				</div>
			</header>

			<div bind:this={scroller} class="flex-1 overflow-y-auto px-4 py-3 space-y-3 text-xs leading-relaxed">
				{#if messages.length === 0}
					<p class="text-muted">Posez une question sur vos cours, devoirs, notes ou absences, ou demandez-moi d'ajouter un devoir.</p>
					<div class="flex flex-col items-start gap-1.5 pt-1">
						{#each SUGGESTIONS as s}
							<button type="button" onclick={() => send(s)} class="text-left rounded-lg bg-app-raised hover:bg-app-raised2 px-3 py-1.5 text-fg cursor-pointer transition-colors">{s}</button>
						{/each}
					</div>
				{/if}

				{#each messages as m}
					{#if m.role === "user"}
						<div class="flex justify-end">
							<div class="max-w-[85%] rounded-lg bg-cyan-600/15 text-fg px-3 py-2 whitespace-pre-wrap break-words">{m.content}</div>
						</div>
					{:else}
						<div class="text-fg break-words space-y-1">{@html render(m.content)}</div>
					{/if}
				{/each}

				{#if loading}
					<div class="flex items-center gap-1 text-subtle" aria-live="polite">
						<span class="w-1.5 h-1.5 rounded-full bg-current animate-bounce"></span>
						<span class="w-1.5 h-1.5 rounded-full bg-current animate-bounce [animation-delay:120ms]"></span>
						<span class="w-1.5 h-1.5 rounded-full bg-current animate-bounce [animation-delay:240ms]"></span>
					</div>
				{/if}
				{#if error}
					<p class="text-red-400">{error}</p>
				{/if}
			</div>

			<form
				class="flex items-end gap-2 p-3 border-t border-app-border"
				onsubmit={(e) => {
					e.preventDefault();
					send(input);
				}}
			>
				<textarea
					bind:value={input}
					onkeydown={onKeydown}
					rows="1"
					maxlength="500"
					placeholder="Votre question…"
					aria-label="Votre question"
					class="flex-1 resize-none max-h-24 rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
				></textarea>
				<button
					type="submit"
					disabled={loading || !input.trim()}
					aria-label="Envoyer"
					class="w-9 h-9 shrink-0 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white flex items-center justify-center cursor-pointer"
				>
					<Send class="w-4 h-4" />
				</button>
			</form>
		</section>
	{/if}
{/if}
