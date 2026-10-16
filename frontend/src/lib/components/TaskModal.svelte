<script lang="ts">
	import Modal from "./Modal.svelte";
	import Button from "./Button.svelte";
	import { api } from "$lib/api";

	let {
		open = $bindable(false),
		onTaskCreated
	}: {
		open: boolean;
		onTaskCreated?: () => void;
	} = $props();

	let title = $state("");
	let description = $state("");
	let subject = $state("R101 Réseaux");
	let event_type = $state("ds");
	let due_date = $state("");
	let isSubmitting = $state(false);
	let error = $state("");

	const subjectsList = [
		"R101 Réseaux",
		"R102 Principes architecture",
		"R103 Réseaux locaux",
		"R104 Électronique",
		"R105 Support transmission",
		"R106 Archi des systèmes",
		"R107 Programmation",
		"R108 Systèmes exploitation",
		"R109 Technologies Web",
		"R110 Anglais",
		"R111 Expression-Communication",
		"R112 Projet Personnel Pro (PPP)",
		"R113 Maths du signal",
		"R114 Maths des transmissions",
		"R115 Gestion de projet",
		"SAÉ S1.01",
		"SAÉ S1.02",
		"Autre"
	];

	function initDate() {
		const tomorrow = new Date();
		tomorrow.setDate(tomorrow.getDate() + 1);
		tomorrow.setHours(8, 0, 0, 0);
		due_date = tomorrow.toISOString().slice(0, 16);
	}

	$effect(() => {
		if (open && !due_date) {
			initDate();
		}
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		isSubmitting = true;
		error = "";

		try {
			await api.createTask({
				title,
				subject,
				event_type,
				due_date: new Date(due_date).toISOString(),
				description: description.trim() || undefined,
				status: "todo"
			});
			open = false;
			title = "";
			description = "";
			if (onTaskCreated) onTaskCreated();
		} catch (err: any) {
			error = err.message || "Erreur lors de la création de la tâche.";
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Modal bind:open title="Ajouter un Événement ou un DS" description="Planifiez vos contrôles, rendus de TP ou rappels personnels.">
	<form onsubmit={handleSubmit} class="space-y-4">
		{#if error}
			<div class="rounded-lg bg-red-600/20 p-3 text-xs text-red-300 font-medium">
				{error}
			</div>
		{/if}

		<div>
			<label for="task-type" class="block text-xs font-medium text-zinc-400 mb-1.5">Type d'évaluation</label>
			<div class="grid grid-cols-4 gap-2">
				{#each [
					{ id: 'ds', label: 'Devoir Surveillé (DS)' },
					{ id: 'dm', label: 'Devoir Maison (DM)' },
					{ id: 'tp', label: 'TP Noté' },
					{ id: 'todo', label: 'Rappel / To-Do' }
				] as item}
					<button
						type="button"
						onclick={() => (event_type = item.id)}
						class="rounded-lg px-2 py-2 text-xs font-medium text-center transition-all cursor-pointer {event_type === item.id ? 'bg-white/[0.08] text-white font-semibold shadow-xs' : 'border border-app-border bg-app-surface text-zinc-400 hover:text-white hover:bg-white/[0.03]'}"
					>
						{item.label}
					</button>
				{/each}
			</div>
		</div>

		<div>
			<label for="task-title" class="block text-xs font-medium text-zinc-400 mb-1">Titre de l'épreuve / tâche *</label>
			<input
				id="task-title"
				type="text"
				bind:value={title}
				placeholder="Ex: DS 2 - Routage OSPF & Adressage VLSM"
				required
				class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none"
			/>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
			<div>
				<label for="task-subject" class="block text-xs font-medium text-zinc-400 mb-1">Matière associée</label>
				<select
					id="task-subject"
					bind:value={subject}
					class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
				>
					{#each subjectsList as sub}
						<option value={sub}>{sub}</option>
					{/each}
				</select>
			</div>

			<div>
				<label for="task-date" class="block text-xs font-medium text-zinc-400 mb-1">Date et heure limite *</label>
				<input
					id="task-date"
					type="datetime-local"
					bind:value={due_date}
					required
					class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
				/>
			</div>
		</div>

		<div>
			<label for="task-desc" class="block text-xs font-medium text-zinc-400 mb-1">Consignes ou notes (facultatif)</label>
			<textarea
				id="task-desc"
				bind:value={description}
				rows="3"
				placeholder="Chapitres à réviser, calculatrice autorisée, salle de l'examen..."
				class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none resize-none"
			></textarea>
		</div>

		<div class="flex justify-end gap-2 pt-2 border-t border-app-border">
			<button
				type="button"
				onclick={() => (open = false)}
				disabled={isSubmitting}
				class="px-3.5 py-1.5 rounded-lg border border-app-border bg-app-surface hover:bg-white/[0.04] text-xs font-medium text-zinc-300 transition-colors cursor-pointer"
			>
				Annuler
			</button>
			<button
				type="submit"
				disabled={isSubmitting}
				class="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
			>
				{isSubmitting ? "Enregistrement..." : "Enregistrer le DS"}
			</button>
		</div>
	</form>
</Modal>
