import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder } from '@angular/forms';
import { Color } from '../models/color';
import { Mode } from '../models/mode';
import { Deck } from '../models/deck';

@Component({
  selector: 'app-deck-form',
  template: `
    <form [formGroup]="formDeck" (ngSubmit)="onSubmit(formDeck)">
      <fieldset class="fieldset-magic" formGroupName="deck_colors">
        <legend> Colors </legend>        
            <div *ngFor="let color of colors;">
              <input class="form-component" type="checkbox" [formControlName]="color.name"/>
              <label class="form-component" [for]="color.name">{{color.name}}</label>
            </div>        
        </fieldset>

        <fieldset class="fieldset-magic">
        <legend> Mode </legend>
          <div *ngFor="let mode of modes; let i = index;">                        
            <input class="form-component" type="radio" formControlName="deck_modes" [value]="mode.name" [checked]="i==0"/>
            <label class="form-component" [for]="mode.name">{{mode.name}}</label>
          </div>        
        </fieldset>
    
      <div class="full-width"> 
        <button type="submit"> Create </button>
      </div>
    </form>
  `,
  styleUrls: ['./deck-form.component.css']
})
export class DeckFormComponent implements OnInit {
  @Input() colors: Color[] = [];
  @Input() modes: Mode[] = [];
  @Output()  create: EventEmitter<Deck> = new EventEmitter<Deck>();
  formDeck: FormGroup;  

  constructor(private fb: FormBuilder) {}

  ngOnInit() {
    let initMode = ''
    if (this.modes.length > 0) {
      initMode = this.modes[0].name;
    }
    this.formDeck = this.fb.group({
      deck_colors: this.fb.group({}),      
      deck_modes: initMode,
    });    

    this.colors.forEach(color => {
      (this.formDeck.controls.deck_colors as FormGroup).addControl(color.name, this.fb.control(false))
    }); 
  }

  onSubmit(form: FormGroup) {
    const colors: string[] = Object
		  .keys(form.value.deck_colors)
		  .filter(color => form.value.deck_colors[color]);
    
    this.create.emit(Deck.createDeck(colors, form.value.deck_modes));
  }
}
