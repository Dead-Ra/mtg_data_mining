import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http'; 
import { ReactiveFormsModule } from '@angular/forms';

import {NgxPaginationModule} from 'ngx-pagination'; //https://github.com/michaelbromley/ngx-pagination
import { NgDragDropModule } from 'ng-drag-drop';

import { AppComponent } from './app.component';
import { CardviewComponent } from './cardview/cardview.component';
import { CardsviewComponent } from './cardsview/cardsview.component';
import { AppRoutingModule } from './/app-routing.module';
import { RecommendationComponent } from './recommendation/recommendation.component';
import { RecommendationviewComponent } from './recommendationview/recommendationview.component';
import { RecommendationChildGameComponent } from './recommendation-child-game/recommendation-child-game.component';
import { RecommendationChildColorComponent } from './recommendation-child-color/recommendation-child-color.component';
import { SelectColorsComponent } from './select-colors/select-colors.component';
import { CardsindexComponent } from './cardsindex/cardsindex.component';
import { SelectTypesComponent } from './select-types/select-types.component';
import { SelectModeComponent } from './select-mode/select-mode.component';
import { SpinnerComponent } from './spinner/spinner.component';
import { InputCardsComponent } from './input-cards/input-cards.component';
import { TempMatrixComponent } from './temp-matrix/temp-matrix.component';
import { DeckViewComponent } from './deck-view/deck-view.component';
import { DeckConfigComponent } from './deck-config/deck-config.component';
import { DeckFormComponent } from './deck-form/deck-form.component';
import { DeckAttributesComponent } from './deck-attributes/deck-attributes.component';

@NgModule({
  declarations: [
    AppComponent,
    CardviewComponent,
    CardsviewComponent,
    RecommendationComponent,
    RecommendationviewComponent,
    RecommendationChildGameComponent,
    RecommendationChildColorComponent,
    SelectColorsComponent,
    CardsindexComponent,
    SelectTypesComponent,
    SelectModeComponent,
    SpinnerComponent,
    InputCardsComponent,    
    TempMatrixComponent, DeckViewComponent, DeckConfigComponent, DeckFormComponent, DeckAttributesComponent    
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    NgxPaginationModule,
    ReactiveFormsModule,
    NgDragDropModule.forRoot()
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
