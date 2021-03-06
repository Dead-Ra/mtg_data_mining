import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { map, publishReplay, refCount, catchError } from 'rxjs/operators';
import { compareCardsFn, filterColorsTypesNameFn } from './card.utils';
import { Card } from './models/card';

@Injectable({
  providedIn: 'root'
})
export class CardService {

  _cards: Observable<Card[]>;

  constructor(private http: HttpClient) { }

  loadCards(colors: string[], mode: string): Observable<Card[]> {
    if (!this._cards) {
      const filename = 'catalog_' + mode + '_' + colors.join('_');
      this._cards = this.http.get<Card[]>('./assets/' + filename + '.json')
      .pipe(
        map(cards => cards.sort(compareCardsFn)),
        publishReplay(),
        refCount(),
        catchError(this.handleError)
      );
    }
    return this._cards;
  }

  cleanCache() {
    this._cards = null;
  }

  getCards(filterColors: string[] = [], filterTypes: string[] = [], filterName: string = '', filterSecondaryColors: string[] = []): Observable<Card[]> {
    return this._cards.pipe(
      map(cards => cards.filter(card => filterColorsTypesNameFn(card, filterColors, filterTypes, filterName, filterSecondaryColors)))
    );
  }

  getCard(id: number): Observable<Card> {
    return this.getCards().pipe(map(cards => cards.filter(card => card.multiverseid === id).pop()));
  }

  getCardsById(ids: number[], filterColors: string[] = [], filterTypes: string[] = [], filterName: string = '', filterSecondaryColors: string[] = []): Observable<Card []> {
    return this.getCards()    
      .pipe(
        map(cards => cards.filter(card => ids.includes(card.multiverseid))),
        map(cards => cards.filter(card => filterColorsTypesNameFn(card, filterColors, filterTypes, filterName, filterSecondaryColors))));
  }

  private handleError(error: HttpErrorResponse) {
    return throwError(
      'Something bad happened; please try again later.');
  };
}
