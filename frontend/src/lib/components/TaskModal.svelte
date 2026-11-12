<script lang="ts">
	import Modal from "./Modal.svelte";
	import Button from "./Button.svelte";
	import DateTimePicker from "./DateTimePicker.svelte";
	import { api } from "$lib/api";

	let {
		open = $bindable(false),
		task = null,
		prefill = null,
		onTaskCreated,
		onTaskSaved
	}: {
		open: boolean;
		task?: any;
		prefill?: { subject?: string; event_type?: string; due_date?: string } | null;
		onTaskCreated?: () => void;
		onTaskSaved?: () => void;
	} = $props();

	let title = $state("");
	let description = $state("");
	let subject = $state("");
	let event_type = $state("ds");
	let due_date = $state("");
	let isSubmitting = $state(false);
	let error = $state("");

	// Matieres proposees : celles du releve ScoDoc de l'utilisateur (saisie libre possible).
	let subjectsList = $state<string[]>([]);

	$effect(() => {
		if (!open || subjectsList.length) return;
		api.getGrades()
			.then((data) => {
				subjectsList = (data?.matieres ?? []).map((m: any) => `${m.code} ${m.titre}`.trim()).filter(Boolean);
			})
			.catch(() => {});
	});

	// Rattache un intitule de cours ("R113 Maths du signal-TDB") a la matiere du releve via son code.
	function resolveSubject(raw: string): string {
		const code = raw.match(/^(R\d{3}|SA[EÉ]\s*S?[\d.]+)/i)?.[1]?.toUpperCase().replace(/\s+/g, " ");
		const found = code ? subjectsList.find((s) => s.toUpperCase().startsWith(code)) : undefined;
		return found ?? raw;
	}

	function initDefaultDate() {
		const tomorrow = new Date();
		tomorrow.setDate(tomorrow.getDate() + 1);
		tomorrow.setHours(8, 0, 0, 0);
		due_date = new Date(tomorrow.getTime() - tomorrow.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
	}

	$effect(() => {
		if (open) {
			error = "";
			if (task) {
				title = task.title || "";
				description = task.description || "";
				subject = task.subject || "";
				event_type = task.event_type || (task.category && task.category !== "AUTRES" ? task.category.toLowerCase() : task.category ? "todo" : "ds");
				if (task.due_date) {
					try {
						const d = new Date(task.due_date);
						due_date = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
					} catch {
						initDefaultDate();
					}
				} else {
					initDefaultDate();
				}
			} else {
				title = "";
				description = "";
				subject = prefill?.subject ? resolveSubject(prefill.subject) : "";
				event_type = prefill?.event_type ?? "ds";
				// dt_start est une heure locale sans fuseau ("2026-11-10T09:00:00") : compatible avec datetime-local
				if (prefill?.due_date) due_date = prefill.due_date.slice(0, 16);
				else initDefaultDate();
			}
		}
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		isSubmitting = true;
		error = "";

		try {
			if (task && (task.task_id || task.id)) {
				const idToUpdate = task.task_id || (typeof task.id === "number" ? task.id : parseInt(String(task.id).replace("personal-", ""), 10));
				await api.updateTask(idToUpdate, {
					title,
					subject,
					event_type,
					due_date: new Date(due_date).toISOString(),
					description: description.trim() || undefined
				});
			} else {
				await api.createTask({
					title,
					subject,
					event_type,
					due_date: new Date(due_date).toISOString(),
					description: description.trim() || undefined,
					status: "todo"
				});
			}
			open = false;
			title = "";
			description = "";
			if (onTaskSaved) onTaskSaved();
			if (onTaskCreated) onTaskCreated();
		} catch (err: any) {
			error = err.message || "Erreur lors de l'enregistrement du devoir.";
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Modal
	bind:open
	title={task ? "Modifier le devoir" : "Ajouter un devoir"}
	description={task ? "Modifiez les informations de ce devoir." : "Planifiez vos devoirs, contrôles ou rappels."}
>
	<form onsubmit={handleSubmit} class="space-y-4">
		{#if error}
			<div class="rounded-lg bg-red-600/20 p-3 text-xs text-red-300 font-medium">
				{error}
			</div>
		{/if}

		<div>
			<label for="task-type" class="block text-xs font-medium text-muted mb-1.5">Catégorie</label>
			<div class="grid grid-cols-4 gap-2">
				{#each [
					{ id: 'ds', label: 'DS' },
					{ id: 'dm', label: 'DM' },
					{ id: 'tp', label: 'TP' },
					{ id: 'todo', label: 'Autres' }
				] as item}
					<button
						type="button"
						onclick={() => (event_type = item.id)}
						class="rounded-lg px-2 py-2 text-xs font-medium text-center transition-all cursor-pointer {event_type === item.id ? 'bg-fg/[0.08] text-fg font-semibold shadow-xs' : 'border border-app-border bg-app-surface text-muted hover:text-fg hover:bg-fg/[0.03]'}"
					>
						{item.label}
					</button>
				{/each}
			</div>
		</div>

		<div>
			<label for="task-title" class="block text-xs font-medium text-muted mb-1">Titre de l'épreuve / tâche *</label>
			<input
				id="task-title"
				type="text"
				bind:value={title}
				placeholder="Ex: DS 2 - Routage OSPF & Adressage VLSM"
				required
				class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
			/>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
			<div>
				<label for="task-subject" class="block text-xs font-medium text-muted mb-1">Matière associée</label>
				<input
					id="task-subject"
					type="text"
					list="task-subject-list"
					maxlength="100"
					bind:value={subject}
					placeholder="Choisir ou saisir une matière"
					class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
				/>
				<datalist id="task-subject-list">
					{#each subjectsList as sub}
						<option value={sub}></option>
					{/each}
				</datalist>
			</div>

			<div>
				<label for="task-date" class="block text-xs font-medium text-muted mb-1">Date et heure limite *</label>
				<DateTimePicker id="task-date" bind:value={due_date} />
			</div>
		</div>

		<div>
			<label for="task-desc" class="block text-xs font-medium text-muted mb-1">Consignes ou notes (facultatif)</label>
			<textarea
				id="task-desc"
				bind:value={description}
				rows="3"
				placeholder="Chapitres à réviser, calculatrice autorisée, salle de l'examen..."
				class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none resize-none"
			></textarea>
		</div>

		<div class="flex justify-end gap-2 pt-2 border-t border-app-border">
			<button
				type="button"
				onclick={() => (open = false)}
				disabled={isSubmitting}
				class="px-3.5 py-1.5 rounded-lg border border-app-border bg-app-surface hover:bg-fg/[0.04] text-xs font-medium text-muted transition-colors cursor-pointer"
			>
				Annuler
			</button>
			<button
				type="submit"
				disabled={isSubmitting}
				class="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
			>
				{isSubmitting ? "Enregistrement..." : (task ? "Enregistrer les modifications" : "Enregistrer le devoir")}
			</button>
		</div>
	</form>
</Modal>
