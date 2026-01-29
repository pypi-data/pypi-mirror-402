import typing

import numpy
import torch
import sklearn.base
import sklearn.metrics

import cvtda.utils
import cvtda.logging
import cvtda.neural_network


class MultiImageDataset:
    def __init__(self, features, labels, images):
        self.labels = torch.tensor(labels, dtype = torch.long)
        self.features = torch.tensor(features, dtype = torch.float32)
        self.images = [ torch.tensor(imgs, dtype = torch.float32).permute((0, 3, 1, 2)) for imgs in images ]


class MultiImageClassifier(sklearn.base.ClassifierMixin):
    def __init__(
        self,

        n_jobs: int = -1,
        random_state: int = 42,

        device: torch.device = torch.device("cuda"),
        batch_size: int = 256,
        learning_rate: float = 1e-3,
        n_epochs: int = 100,
        
        skip_images: bool = False,
        skip_features: bool = False
    ):
        self.n_jobs_ = n_jobs
        self.random_state_ = random_state

        self.device_ = device
        self.batch_size_ = batch_size
        self.learning_rate_ = learning_rate
        self.n_epochs_ = n_epochs

        self.skip_images_ = skip_images
        self.skip_features_ = skip_features


    def fit(self, train: MultiImageDataset, val: typing.Optional[MultiImageDataset]):
        cvtda.utils.set_random_seed(self.random_state_)
        train_dl = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(train.labels, train.features, *train.images),
            batch_size = self.batch_size_,
            shuffle = True
        )
        self.init_(*next(iter(train_dl)))

        for epoch in range(self.n_epochs_):
            sum_loss = 0

            self.model_list_.train()
            for (labels, features, *images) in cvtda.logging.logger().pbar(train_dl, desc = f"Epoch {epoch}"):
                self.optimizer_.zero_grad()
                pred = self.forward_(features, *images)
                loss = torch.nn.functional.cross_entropy(pred, labels.to(self.device_), reduction = 'mean')
                loss.backward()
                self.optimizer_.step()
                sum_loss += loss.item()
            postfix = { 'loss': sum_loss, 'lr': self.optimizer_.param_groups[0]['lr'] }
            self.scheduler_.step()

            if val is not None:
                val_proba = self.predict_proba_(val)
                val_pred = numpy.argmax(val_proba, axis = 1)
                postfix['val_acc'] = sklearn.metrics.accuracy_score(val.labels, val_pred)

            cvtda.logging.logger().print(f"Epoch {epoch}:", postfix)

        self.fitted_ = True
        return self
    
    def predict_proba(self, dataset: cvtda.neural_network.Dataset) -> numpy.ndarray:
        assert self.fitted_ is True, 'fit() must be called before predict_proba()'
        cvtda.utils.set_random_seed(self.random_state_)
        return self.predict_proba_(dataset)


    def init_(
        self, 
        labels: torch.Tensor,
        features: torch.Tensor,
        *images: typing.List[torch.Tensor]
    ):
        self.features_base_ = cvtda.neural_network.NNBase(
            num_diagrams = 0, skip_diagrams = True, skip_images = True, skip_features = False
        ).to(self.device_).train()

        self.images_bases_ = torch.nn.ModuleList([
            cvtda.neural_network.NNBase(
                num_diagrams = 0, skip_diagrams = True, skip_images = False, skip_features = True
            ).to(self.device_).train()
            for _ in range(len(images))
        ])

        self.model_ = torch.nn.Sequential(
            torch.nn.Dropout(0.4), torch.nn.LazyLinear(256), torch.nn.BatchNorm1d(256), torch.nn.GELU(),
            torch.nn.Dropout(0.3), torch.nn.Linear(256, 128), torch.nn.BatchNorm1d(128), torch.nn.GELU(),
            torch.nn.Dropout(0.2), torch.nn.Linear(128, 64), torch.nn.BatchNorm1d(64), torch.nn.GELU(),
            torch.nn.Dropout(0.1), torch.nn.Linear(64, 32), torch.nn.BatchNorm1d(32), torch.nn.GELU(),
            torch.nn.Linear(32, len(torch.unique(labels)))
        ).to(self.device_).train()

        self.model_list_ = torch.nn.ModuleList([ self.features_base_, self.images_bases_, self.model_ ])

        self.optimizer_ = torch.optim.AdamW(
            params = self.model_list_.parameters(),
            lr = self.learning_rate_
        )
        
        def lr_scheduler_lambda(epoch):
            if epoch < self.n_epochs_ // 10:
                return 1
            if epoch < self.n_epochs_ // 4:
                return 0.1
            if epoch < self.n_epochs_ // 2:
                return 0.01
            if epoch < 3 * self.n_epochs_ // 4:
                return 0.001
            return 0.0001
        self.scheduler_ = torch.optim.lr_scheduler.LambdaLR(self.optimizer_, lr_scheduler_lambda)

        features_result = self.features_base_(None, features.to(self.device_))
        images_result = [ self.images_bases_[i](images[i].to(self.device_), None) for i in range(len(images)) ]

        result = []
        if not self.skip_features_:
            result.append(features_result)
        if not self.skip_images_:
            result.extend(images_result)
        self.model_(torch.cat(result, dim = 1))

        cvtda.logging.logger().print(f'Input to LazyLinear: {self.model_[1].in_features}')
        cvtda.logging.logger().print(f'Parameters: {sum(p.numel() for p in self.model_list_.parameters())}')

    def forward_(
        self,
        features: torch.Tensor,
        *images: typing.List[torch.Tensor]
    ) -> torch.Tensor:
        result = []

        if not self.skip_features_:
            result.append(self.features_base_(None, features.to(self.device_)))

        if not self.skip_images_:
            result.extend([ self.images_bases_[i](images[i].to(self.device_), None) for i in range(len(images)) ])

        return self.model_(torch.cat(result, dim = 1))

    def predict_proba_(self, dataset: cvtda.neural_network.Dataset) -> numpy.ndarray:
        dl = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(dataset.features, *dataset.images),
            batch_size = self.batch_size_,
            shuffle = False
        )

        y_pred_proba = [ ]
        self.model_list_.eval()
        with torch.no_grad():
            for (features, *images) in dl:
                y_pred_proba.append(self.forward_(features, *images))
        y_pred_proba = torch.vstack(y_pred_proba)
        return torch.nn.functional.softmax(y_pred_proba, dim = 1).cpu().numpy()
